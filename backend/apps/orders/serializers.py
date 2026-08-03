"""Serializers for orders, order items and status history.

Ownership of validation lives here: the backend validates customer, garments,
quantities, prices, dates, measurement selection/completeness and the status
lifecycle. Frontend validation is never a security boundary.
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.billing.services import order_payment_summary
from apps.customers.models import (
    GARMENT_ALLOWED_FIELDS,
    GARMENT_REQUIRED_FIELDS,
    Customer,
    GarmentType,
    Measurement,
)
from apps.customers.serializers import CustomerSerializer
from apps.orders.models import (
    ALLOWED_TRANSITIONS,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
)

MAX_NOTES_LENGTH = 4000
MAX_ITEM_NOTES_LENGTH = 2000
MIN_PRICE = Decimal("0.00")


class OrderItemSerializer(serializers.ModelSerializer):
    """Read representation of an order line item."""

    garment_type = serializers.CharField(
        source="get_garment_type_display", read_only=True
    )
    garment_code = serializers.CharField(source="garment_type", read_only=True)
    measurement_id = serializers.IntegerField(read_only=True)
    line_total = serializers.SerializerMethodField()
    assigned_quantity = serializers.SerializerMethodField()
    remaining_quantity = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "garment_type",
            "garment_code",
            "quantity",
            "assigned_quantity",
            "remaining_quantity",
            "measurement_id",
            "measurement_version",
            "measurement_snapshot",
            "unit_price",
            "line_total",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_line_total(self, obj):
        return obj.amount

    def get_assigned_quantity(self, obj):
        total = Decimal("0")
        for assignment in obj.work_assignments.all():
            total += assignment.assigned_quantity
        return total

    def get_remaining_quantity(self, obj):
        total = Decimal("0")
        for assignment in obj.work_assignments.all():
            total += assignment.assigned_quantity
        return obj.quantity - total


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Read representation of a status history entry."""

    from_status = serializers.CharField(required=False, allow_null=True)
    to_status = serializers.CharField()
    changed_by_username = serializers.CharField(
        source="changed_by.username", read_only=True, default=None
    )

    class Meta:
        model = OrderStatusHistory
        fields = (
            "id",
            "from_status",
            "to_status",
            "changed_by",
            "changed_by_username",
            "changed_at",
        )
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Read representation of an order with nested items and history."""

    customer = CustomerSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    garment_summary = serializers.SerializerMethodField()
    payment_summary = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "customer",
            "order_date",
            "expected_delivery_date",
            "status",
            "notes",
            "total_amount",
            "collected_at",
            "garment_summary",
            "payment_summary",
            "items",
            "status_history",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_garment_summary(self, obj):
        summary = []
        for item in obj.items.all():
            summary.append(
                {
                    "garment_type": item.garment_type,
                    "quantity": item.quantity,
                }
            )
        return summary

    def get_payment_summary(self, obj):
        """Authoritative billing totals for this order (detail views only).

        Populated on the order detail endpoint where the invoice exists; the
        backend stays authoritative for order total / paid / outstanding /
        status. Returns ``None`` on list responses to keep them light.
        """
        if not self.context.get("include_payment_summary"):
            return None
        return order_payment_summary(obj)


class OrderItemCreateSerializer(serializers.Serializer):
    """Validated input for a single garment line on a new order."""

    garment_type = serializers.ChoiceField(choices=GarmentType.choices)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=MIN_PRICE
    )
    measurement_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(
        required=False, allow_blank=True, max_length=MAX_ITEM_NOTES_LENGTH
    )


class OrderCreateSerializer(serializers.Serializer):
    """Create an order with one or more garment items and valid measurements.

    The customer must exist and be active. Each item must reference an existing
    measurement row belonging to that customer and matching the item garment,
    and that measurement must contain all values required for the garment.
    """

    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    order_date = serializers.DateField(required=False)
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(
        required=False, allow_blank=True, max_length=MAX_NOTES_LENGTH
    )
    items = OrderItemCreateSerializer(many=True)

    def validate_customer(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Archived customers cannot place new orders. Restore the customer first."
            )
        return value

    def validate(self, attrs):
        if not attrs.get("items"):
            raise serializers.ValidationError(
                {"items": "An order must contain at least one garment item."}
            )
        order_date = attrs.get("order_date", timezone.localdate())
        expected = attrs.get("expected_delivery_date")
        if expected and expected < order_date:
            raise serializers.ValidationError(
                {
                    "expected_delivery_date": (
                        "Expected delivery date cannot be earlier than the order date."
                    )
                }
            )
        self._resolve_items(attrs)
        return attrs

    def _resolve_items(self, attrs):
        """Bind each item to its Measurement row and validate it fully."""
        customer = attrs["customer"]
        resolved = []
        for index, item in enumerate(attrs["items"]):
            garment = item["garment_type"]
            measurement_id = item.get("measurement_id")

            measurement = None
            if measurement_id is not None:
                try:
                    measurement = Measurement.objects.get(pk=measurement_id)
                except Measurement.DoesNotExist:
                    raise serializers.ValidationError(
                        {
                            "items": {
                                index: {
                                    "measurement_id": "Selected measurement does not exist."
                                }
                            }
                        }
                    )
                if measurement.customer_id != customer.id:
                    raise serializers.ValidationError(
                        {
                            "items": {
                                index: {
                                    "measurement_id": (
                                        "Selected measurement does not belong to the "
                                        "chosen customer."
                                    )
                                }
                            }
                        }
                    )
                if measurement.garment_type != garment:
                    raise serializers.ValidationError(
                        {
                            "items": {
                                index: {
                                    "measurement_id": (
                                        f"Selected measurement is a "
                                        f"{measurement.get_garment_type_display()} "
                                        f"measurement, not {GarmentType(garment).label}."
                                    )
                                }
                            }
                        }
                    )
                missing = [
                    field_name
                    for field_name in GARMENT_REQUIRED_FIELDS[garment]
                    if getattr(measurement, field_name, None) is None
                ]
                if missing:
                    raise serializers.ValidationError(
                        {
                            "items": {
                                index: {
                                    "measurement_id": (
                                        f"The selected {GarmentType(garment).label} "
                                        "measurement is incomplete. "
                                        "Record the missing values on the customer's "
                                        "measurement page before creating this order."
                                    )
                                }
                            }
                        }
                    )
            else:
                raise serializers.ValidationError(
                    {
                        "items": {
                            index: {
                                "measurement_id": (
                                    f"A measurement is required for each "
                                    f"{GarmentType(garment).label} item. "
                                    "Select a measurement version or record one for the "
                                    "customer first."
                                )
                            }
                        }
                    }
                )
            item["measurement"] = measurement
            resolved.append(item)
        attrs["items"] = resolved

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        customer = validated_data["customer"]
        request_user = getattr(self.context.get("request"), "user", None)
        with transaction.atomic():
            order = Order.objects.create(**validated_data)

            order_items = []
            for item_data in items_data:
                measurement = item_data.pop("measurement")
                snapshot = None
                if measurement is not None:
                    allowed = GARMENT_ALLOWED_FIELDS[item_data["garment_type"]]
                    snapshot = {
                        field_name: (
                            float(getattr(measurement, field_name))
                            if getattr(measurement, field_name) is not None
                            else None
                        )
                        for field_name in allowed
                    }
                order_items.append(
                    OrderItem(
                        order=order,
                        measurement=measurement,
                        measurement_version=(
                            measurement.version if measurement else None
                        ),
                        measurement_snapshot=snapshot,
                        **item_data,
                    )
                )
            OrderItem.objects.bulk_create(order_items)

            order.total_amount = sum(
                (item.unit_price * item.quantity for item in order_items),
                Decimal("0.00"),
            )
            order.save(update_fields=["total_amount"])

            OrderStatusHistory.objects.create(
                order=order,
                from_status=None,
                to_status=OrderStatus.NEW,
                changed_by=request_user if request_user.is_authenticated else None,
            )
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Safe partial update: only notes and expected delivery date are editable.

    Status, customer, items, dates and amounts are intentionally immutable after
    creation to preserve the recorded order. Status changes go through the
    dedicated status action only.
    """

    class Meta:
        model = Order
        fields = ("notes", "expected_delivery_date")
        extra_kwargs = {
            "notes": {
                "max_length": MAX_NOTES_LENGTH,
                "allow_blank": True,
                "required": False,
                "trim_whitespace": False,
            },
            "expected_delivery_date": {
                "required": False,
                "allow_null": True,
            },
        }

    def validate_expected_delivery_date(self, value):
        order = self.instance
        if value and order and value < order.order_date:
            raise serializers.ValidationError(
                "Expected delivery date cannot be earlier than the order date."
            )
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Validate a status transition request (STAFF only)."""

    status = serializers.ChoiceField(choices=OrderStatus.choices)

    def validate_status(self, value):
        order = self.context.get("order")
        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid status transition from {order.get_status_display()} "
                f"to {OrderStatus(value).label}. Allowed: "
                + (
                    ", ".join(OrderStatus(s).label for s in sorted(allowed))
                    if allowed
                    else "none (this order is in a terminal state)."
                )
            )
        return value
