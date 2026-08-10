"""Serializers for income and expense records."""

from decimal import Decimal

from rest_framework import serializers

from apps.billing.models import CustomerPayment

from .models import Expense


class IncomeSerializer(serializers.ModelSerializer):
    """Customer-derived income entry backed by an append-only payment.

    Each payment contributes to income exactly once: ADVANCE / PARTIAL / FINAL
    payments are positive and every REFUND transaction is presented with a
    negative ``net_amount``, so the read-only income view shows refunds as
    reducing net income. Every value here is derived from payment data - the
    client never supplies financial totals or ``recorded_by``.
    """

    payment_type_display = serializers.CharField(
        source="get_payment_type_display", read_only=True
    )
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    invoice_id = serializers.IntegerField(read_only=True)
    invoice_number = serializers.CharField(
        source="invoice.invoice_number", read_only=True
    )
    order_id = serializers.IntegerField(
        source="invoice.order_id", read_only=True
    )
    order_number = serializers.CharField(
        source="invoice.order.order_number", read_only=True
    )
    customer_id = serializers.IntegerField(
        source="invoice.order.customer_id", read_only=True
    )
    customer_name = serializers.CharField(
        source="invoice.order.customer.full_name", read_only=True
    )
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    recorded_by_name = serializers.SerializerMethodField()
    net_amount = serializers.SerializerMethodField()

    class Meta:
        model = CustomerPayment
        fields = [
            "id",
            "payment_type",
            "payment_type_display",
            "payment_method",
            "payment_method_display",
            "amount",
            "net_amount",
            "payment_date",
            "invoice_id",
            "invoice_number",
            "order_id",
            "order_number",
            "customer_id",
            "customer_name",
            "reference",
            "notes",
            "recorded_by",
            "recorded_by_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_recorded_by_name(self, obj):
        return obj.recorded_by.username if obj.recorded_by else None

    def get_net_amount(self, obj):
        if obj.payment_type == CustomerPayment.PaymentType.REFUND:
            return -obj.amount
        return obj.amount


class ExpenseSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    payment_method = serializers.ChoiceField(choices=Expense.Method.choices)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            "id",
            "category",
            "category_display",
            "amount",
            "expense_date",
            "payment_method",
            "payment_method_display",
            "description",
            "reference",
            "recorded_by",
            "recorded_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category_display",
            "payment_method_display",
            "recorded_by",
            "recorded_by_name",
            "created_at",
            "updated_at",
        ]

    def get_recorded_by_name(self, obj):
        return obj.recorded_by.username if obj.recorded_by else None

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Expense amount must be greater than zero."
            )
        return value
