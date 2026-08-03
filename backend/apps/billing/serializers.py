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

from apps.customers.serializers import CustomerSerializer
from apps.orders.models import Order

from .models import CustomerPayment, Invoice, InvoiceItem
from .services import create_invoice_for_order, invoice_summary

MAX_NOTES_LENGTH = 4000


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
            raise serializers.ValidationError(
                "An invoice already exists for this order."
            )
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
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomerPayment
        fields = (
            "id",
            "invoice",
            "invoice_number",
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

    The invoice comes from the URL (never the client) and ``recorded_by`` comes
    from the authenticated user. The service re-validates the amount against the
    locked invoice balance, so the balance check is authoritative.
    """

    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    payment_date = serializers.DateField(required=False)
    payment_method = serializers.ChoiceField(choices=CustomerPayment.Method.choices)
    reference = serializers.CharField(required=False, allow_blank=True, max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )
        return value
