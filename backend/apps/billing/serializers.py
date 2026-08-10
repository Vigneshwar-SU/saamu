"""Serializers for invoices and customer payments.

Validation ownership lives here and on the backend services: the client can
only supply the order reference, invoice date and notes when creating an
invoice, and the amount, payment date, method, reference and notes when
recording a payment. Audit identity (``created_by`` / ``recorded_by``), derived
financial values and item snapshots are always managed server-side and are
never accepted from a client.
"""

from decimal import Decimal

from rest_framework import serializers

from apps.customers.models import Customer
from apps.customers.serializers import CustomerSerializer
from apps.orders.models import Order

from .models import CustomerPayment, Invoice, InvoiceItem, ManualReminder, ShopDetails
from .services import create_invoice_for_order, invoice_summary

MAX_NOTES_LENGTH = 4000
MAX_REMINDER_TITLE_LENGTH = 200
MAX_REMINDER_DESCRIPTION_LENGTH = 4000


class ShopDetailsSerializer(serializers.ModelSerializer):
    """Read/update representation of the singleton shop profile.

    Only the supported shop identity fields are exposed. Validation mirrors
    the model constraints so the Settings UI can never store an empty name or
    an implausible establishment year, keeping the shop block on the digital
    bill real and consistent.
    """

    class Meta:
        model = ShopDetails
        fields = (
            "id",
            "name",
            "tagline",
            "address",
            "phone",
            "established_year",
            "customer_follow_up_months",
        )
        read_only_fields = ("id",)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Shop name is required.")
        return value

    def validate_established_year(self, value):
        if value < 1000 or value > 2100:
            raise serializers.ValidationError(
                "Enter a valid year between 1000 and 2100."
            )
        return value

    def validate_customer_follow_up_months(self, value):
        if value < 1 or value > 60:
            raise serializers.ValidationError(
                "Follow-up threshold must be between 1 and 60 months."
            )
        return value


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Read representation of an immutable invoice line snapshot."""

    class Meta:
        model = InvoiceItem
        fields = (
            "id",
            "garment_type",
            "garment_code",
            "quantity",
            "unit_price",
            "line_total",
        )
        read_only_fields = fields


class InvoiceOrderSerializer(serializers.ModelSerializer):
    """Minimal read-only order summary embedded in an invoice response."""

    class Meta:
        model = Order
        fields = ("id", "order_number", "order_date", "status", "total_amount")
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    """Read representation of an invoice with derived billing values.

    Subtotal, total, amount paid, balance due, status and payment count are
    re-derived from the immutable item snapshots and the append-only payments
    on every read, so the presented values always honour the billing rules.
    """

    customer = CustomerSerializer(source="order.customer", read_only=True)
    order = InvoiceOrderSerializer(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    amount_paid = serializers.SerializerMethodField()
    gross_paid = serializers.SerializerMethodField()
    refunded_amount = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    payment_count = serializers.SerializerMethodField()
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "invoice_date",
            "customer",
            "order",
            "items",
            "subtotal",
            "adjustment_amount",
            "total_amount",
            "gross_paid",
            "refunded_amount",
            "amount_paid",
            "balance_due",
            "status",
            "payment_count",
            "notes",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_gross_paid(self, obj):
        return invoice_summary(obj)["gross_paid"]

    def get_refunded_amount(self, obj):
        return invoice_summary(obj)["refunded_amount"]

    def get_amount_paid(self, obj):
        return invoice_summary(obj)["amount_paid"]

    def get_balance_due(self, obj):
        return invoice_summary(obj)["balance_due"]

    def get_status(self, obj):
        return invoice_summary(obj)["status"]

    def get_payment_count(self, obj):
        return invoice_summary(obj)["payment_count"]

    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        summary = invoice_summary(instance)
        data["subtotal"] = summary["subtotal"]
        data["adjustment_amount"] = summary["adjustment_amount"]
        data["total_amount"] = summary["total_amount"]
        return data


class InvoiceEligibleOrderSerializer(serializers.ModelSerializer):
    """Minimal read-only order summary for the invoice creation dropdown.

    Only orders without an existing invoice are served by the
    ``available-orders`` endpoint, so the client can never pick an
    already-invoiced order from the normal flow. The payload stays light:
    just what the dropdown renders (id, order number, customer) plus the
    figures shown beside the selection.
    """

    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "order_date",
            "status",
            "total_amount",
            "customer",
        )
        read_only_fields = fields


class InvoiceCreateSerializer(serializers.Serializer):
    """Create an invoice from an existing order.

    Only the order reference, invoice date and notes are accepted. The customer
    comes from the order, the line items are snapshotted from the order items,
    the invoice number is generated server-side, and ``created_by`` is always
    taken from the authenticated user.
    """

    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    invoice_date = serializers.DateField(required=False)
    notes = serializers.CharField(
        required=False, allow_blank=True, max_length=MAX_NOTES_LENGTH
    )

    def validate_order(self, value):
        if Invoice.objects.filter(order=value).exists():
            raise serializers.ValidationError("This order already has an invoice.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        return create_invoice_for_order(
            order=validated_data["order"],
            invoice_date=validated_data.get("invoice_date"),
            notes=validated_data.get("notes", ""),
            created_by=user,
        )


class CustomerPaymentSerializer(serializers.ModelSerializer):
    """Read representation of an append-only customer payment."""

    invoice_number = serializers.CharField(
        source="invoice.invoice_number", read_only=True
    )
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    payment_type_display = serializers.CharField(
        source="get_payment_type_display", read_only=True
    )
    refunded_payment = serializers.PrimaryKeyRelatedField(read_only=True)
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomerPayment
        fields = (
            "id",
            "invoice",
            "invoice_number",
            "payment_type",
            "payment_type_display",
            "refunded_payment",
            "amount",
            "payment_date",
            "payment_method",
            "payment_method_display",
            "reference",
            "notes",
            "recorded_by",
            "recorded_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_recorded_by_name(self, obj):
        return obj.recorded_by.username if obj.recorded_by else None


class CustomerPaymentCreateSerializer(serializers.Serializer):
    """Validate a customer payment before the concurrency-safe service runs.

    The invoice comes from the URL (never the client), ``recorded_by`` comes
    from the authenticated user, and ``payment_type`` (ADVANCE / PARTIAL /
    FINAL / REFUND) is optional - when omitted the service derives it from the
    amount. ``refunded_payment`` may reference the original transaction a REFUND
    reverses; cross-field validation happens in the service under the row lock,
    so the balance checks are authoritative.
    """

    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    payment_date = serializers.DateField(required=False)
    payment_method = serializers.ChoiceField(choices=CustomerPayment.Method.choices)
    payment_type = serializers.ChoiceField(
        choices=CustomerPayment.PaymentType.choices, required=False
    )
    refunded_payment = serializers.PrimaryKeyRelatedField(
        queryset=CustomerPayment.objects.all(), required=False, allow_null=True
    )
    reference = serializers.CharField(required=False, allow_blank=True, max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )
        return value

    def validate_refunded_payment(self, value):
        invoice = self.context.get("invoice")
        if invoice is not None and value is not None:
            if value.invoice_id != invoice.id:
                raise serializers.ValidationError(
                    "The refunded payment does not belong to this invoice."
                )
        return value


class ManualReminderSerializer(serializers.ModelSerializer):
    """Read representation of a persisted manual reminder.

    ``customer`` and ``order`` are exposed as lightweight context summaries
    (never the full nested objects) so the reminders page can render the
    reminder without additional requests while keeping payloads small.
    """

    customer = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True, default=None
    )
    completed_by_name = serializers.CharField(
        source="completed_by.username", read_only=True, default=None
    )

    class Meta:
        model = ManualReminder
        fields = (
            "id",
            "title",
            "description",
            "reminder_date",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "customer",
            "order",
            "completed_at",
            "created_by",
            "created_by_name",
            "completed_by",
            "completed_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_customer(self, obj):
        if obj.customer_id is None:
            return None
        return {
            "id": obj.customer.id,
            "full_name": obj.customer.full_name,
        }

    def get_order(self, obj):
        if obj.order_id is None:
            return None
        return {
            "id": obj.order.id,
            "order_number": obj.order.order_number,
            "status": obj.order.status,
        }


class ManualReminderCreateSerializer(serializers.Serializer):
    """Validate and create a persisted manual reminder (STAFF only).

    ``customer`` and ``order`` are optional context links. When an order is
    supplied without a customer, the order's customer is used so the reminder
    always carries a coherent context.
    """

    title = serializers.CharField(max_length=MAX_REMINDER_TITLE_LENGTH)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=MAX_REMINDER_DESCRIPTION_LENGTH,
    )
    reminder_date = serializers.DateField()
    priority = serializers.ChoiceField(
        choices=ManualReminder.Priority.choices, required=False
    )
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), required=False, allow_null=True
    )
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), required=False, allow_null=True
    )

    def validate(self, attrs):
        customer = attrs.get("customer")
        order = attrs.get("order")
        if order is not None and customer is None:
            attrs["customer"] = order.customer
        elif (
            order is not None
            and customer is not None
            and order.customer_id != customer.id
        ):
            raise serializers.ValidationError(
                {
                    "order": (
                        "The selected order does not belong to the selected customer."
                    )
                }
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        return ManualReminder.objects.create(
            **validated_data,
            created_by=(
                request.user if request and request.user.is_authenticated else None
            ),
        )

    def update(self, instance, validated_data):
        editable = (
            "title",
            "description",
            "reminder_date",
            "priority",
            "customer",
            "order",
        )
        for field in editable:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save(update_fields=editable)
        return instance
