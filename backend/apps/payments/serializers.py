"""Serializers for salary advances and payroll payments."""

from decimal import Decimal

from rest_framework import serializers

from apps.tailors.models import Tailor
from apps.tailors.serializers import TailorSerializer

from .models import PayrollPayment, SalaryAdvance


class SalaryAdvanceSerializer(serializers.ModelSerializer):
    tailor = serializers.PrimaryKeyRelatedField(queryset=Tailor.objects.all())
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SalaryAdvance
        fields = [
            "id",
            "tailor",
            "amount",
            "advance_date",
            "status",
            "notes",
            "payroll_entry",
            "deducted_at",
            "recorded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "payroll_entry",
            "deducted_at",
            "recorded_by",
            "created_at",
            "updated_at",
        ]

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Advance amount must be greater than zero."
            )
        return value

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["tailor"] = TailorSerializer(instance.tailor, context=self.context).data
        ret["recorded_by_name"] = (
            instance.recorded_by.username if instance.recorded_by else None
        )
        return ret


class PayrollPaymentSerializer(serializers.ModelSerializer):
    payroll_entry = serializers.PrimaryKeyRelatedField(read_only=True)
    tailor = serializers.PrimaryKeyRelatedField(read_only=True)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PayrollPayment
        fields = [
            "id",
            "payroll_entry",
            "tailor",
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
        ]
        read_only_fields = [
            "id",
            "payroll_entry",
            "tailor",
            "payment_method_display",
            "recorded_by",
            "recorded_by_name",
            "created_at",
            "updated_at",
        ]

    def get_recorded_by_name(self, obj):
        return obj.recorded_by.username if obj.recorded_by else None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["tailor"] = TailorSerializer(instance.tailor, context=self.context).data
        return ret


class PayrollPaymentCreateSerializer(serializers.Serializer):
    """Write payload for recording a payroll payment.

    ``payroll_entry`` and ``tailor`` are never client-provided: they are set
    server-side from the URL entry so the tailor always matches the entry.
    """

    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_date = serializers.DateField()
    payment_method = serializers.ChoiceField(choices=PayrollPayment.Method.choices)
    reference = serializers.CharField(
        required=False, allow_blank=True, max_length=100, default=""
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, max_length=2000, default=""
    )

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )
        return value
