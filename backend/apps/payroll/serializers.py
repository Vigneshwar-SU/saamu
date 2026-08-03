"""Serializers for payroll periods, entries and assignment breakdowns."""

from decimal import Decimal

from django.db import models
from rest_framework import serializers

from apps.payments.services import period_settlement_summary, settlement_summary
from apps.tailors.models import Tailor, WorkAssignment
from apps.tailors.serializers import TailorSerializer

from .models import PayrollEntry, PayrollPeriod


class PayrollPeriodSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = PayrollPeriod
        fields = [
            "id",
            "period_start",
            "period_end",
            "status",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        period_start = attrs.get("period_start")
        period_end = attrs.get("period_end")
        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError(
                {"period_end": "period_end must be on or after period_start."}
            )
        return attrs

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["created_by_name"] = (
            instance.created_by.username if instance.created_by else None
        )
        aggregates = instance.entries.aggregate(
            total_completed_pieces=models.Sum("completed_pieces"),
            total_piece_rate_earnings=models.Sum("piece_rate_earnings"),
            total_attendance_amount=models.Sum("attendance_amount"),
            total_payable=models.Sum("total_payable"),
            entry_count=models.Count("id"),
        )
        ret["total_completed_pieces"] = aggregates["total_completed_pieces"] or 0
        ret["total_piece_rate_earnings"] = aggregates[
            "total_piece_rate_earnings"
        ] or Decimal("0.00")
        ret["total_attendance_amount"] = aggregates[
            "total_attendance_amount"
        ] or Decimal("0.00")
        ret["total_payable"] = aggregates["total_payable"] or Decimal("0.00")
        ret["entry_count"] = aggregates["entry_count"] or 0
        ret["settlement"] = period_settlement_summary(instance)
        return ret


class PayrollEntrySerializer(serializers.ModelSerializer):
    tailor = serializers.PrimaryKeyRelatedField(queryset=Tailor.objects.all())
    payroll_period = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = PayrollEntry
        fields = [
            "id",
            "payroll_period",
            "tailor",
            "present_days",
            "half_days",
            "absent_days",
            "completed_pieces",
            "piece_rate_earnings",
            "attendance_amount",
            "total_payable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "payroll_period",
            "present_days",
            "half_days",
            "absent_days",
            "completed_pieces",
            "piece_rate_earnings",
            "attendance_amount",
            "total_payable",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["tailor"] = TailorSerializer(instance.tailor, context=self.context).data
        ret["settlement"] = settlement_summary(instance)
        return ret


class PayrollAssignmentSerializer(serializers.ModelSerializer):
    """Light assignment row used for tailor-level payroll breakdowns."""

    order_number = serializers.CharField(
        source="order_item.order.order_number", read_only=True
    )
    garment_type = serializers.CharField(
        source="order_item.get_garment_type_display", read_only=True
    )
    garment_code = serializers.CharField(
        source="order_item.garment_type", read_only=True
    )
    earned_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    remaining_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = WorkAssignment
        fields = [
            "id",
            "order_number",
            "garment_type",
            "garment_code",
            "assigned_quantity",
            "completed_quantity",
            "remaining_quantity",
            "rate_per_piece_snapshot",
            "earned_amount",
            "status",
            "completed_at",
        ]
        read_only_fields = fields
