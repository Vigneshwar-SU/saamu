"""Serializers for payroll periods, entries and assignment breakdowns."""

from decimal import Decimal

from django.db import models
from rest_framework import serializers

from apps.payments.services import period_settlement_summary, settlement_summary
from apps.tailors.models import Tailor, WorkAssignment
from apps.tailors.serializers import TailorSerializer

from .models import (
    PayrollEntry,
    PayrollPeriod,
    TailorSalaryConfiguration,
)


class TailorSalaryConfigurationSerializer(serializers.ModelSerializer):
    """Create/read salary configuration records.

    ``FIXED_SALARY`` and ``MIXED`` models require a positive
    ``fixed_salary_amount``; ``PER_GARMENT`` has no fixed component. ``tailor``
    is writable as a primary key and returned embedded. ``created_by`` is set
    server-side and never accepted from the client.
    """

    tailor = serializers.PrimaryKeyRelatedField(queryset=Tailor.objects.all())
    fixed_salary_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.00")
    )

    class Meta:
        model = TailorSalaryConfiguration
        fields = [
            "id",
            "tailor",
            "salary_model",
            "fixed_salary_amount",
            "effective_from",
            "effective_to",
            "is_active",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        salary_model = attrs.get(
            "salary_model",
            getattr(self.instance, "salary_model", None),
        )
        fixed_salary_amount = attrs.get(
            "fixed_salary_amount",
            getattr(self.instance, "fixed_salary_amount", None),
        )
        if salary_model in {
            TailorSalaryConfiguration.SalaryModel.FIXED_SALARY,
            TailorSalaryConfiguration.SalaryModel.MIXED,
        } and (fixed_salary_amount is None or fixed_salary_amount <= 0):
            raise serializers.ValidationError(
                {
                    "fixed_salary_amount": (
                        "A positive fixed salary amount is required for the "
                        "selected salary model."
                    )
                }
            )
        effective_from = attrs.get("effective_from")
        effective_to = attrs.get("effective_to")
        if effective_from and effective_to and effective_from > effective_to:
            raise serializers.ValidationError(
                {"effective_to": "effective_to must be on or after effective_from."}
            )
        return attrs

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["tailor"] = TailorSerializer(instance.tailor, context=self.context).data
        ret["salary_model_display"] = instance.get_salary_model_display()
        ret["created_by_name"] = (
            instance.created_by.username if instance.created_by else None
        )
        return ret


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
        if hasattr(instance, "_total_payable"):
            aggregates = {
                "total_completed_pieces": instance._total_completed_pieces or 0,
                "total_fixed_salary": (instance._total_fixed_salary or Decimal("0.00")),
                "total_piece_rate_earnings": (
                    instance._total_piece_rate_earnings or Decimal("0.00")
                ),
                "total_gross_salary": instance._total_gross_salary or Decimal("0.00"),
                "total_attendance_amount": (
                    instance._total_attendance_amount or Decimal("0.00")
                ),
                "total_payable": instance._total_payable or Decimal("0.00"),
                "entry_count": instance._entry_count or 0,
            }
            settlement = period_settlement_summary(
                instance,
                precomputed={
                    "gross_payable": aggregates["total_payable"],
                    "advance_deductions": (
                        instance._settlement_deductions or Decimal("0.00")
                    ),
                    "payments_recorded": (instance._settlement_paid or Decimal("0.00")),
                    "payment_count": instance._settlement_payment_count or 0,
                },
            )
        else:
            aggregates = instance.entries.aggregate(
                total_completed_pieces=models.Sum("completed_pieces"),
                total_fixed_salary=models.Sum("fixed_salary_amount"),
                total_piece_rate_earnings=models.Sum("piece_rate_earnings"),
                total_gross_salary=models.Sum("gross_salary"),
                total_attendance_amount=models.Sum("attendance_amount"),
                total_payable=models.Sum("total_payable"),
                entry_count=models.Count("id"),
            )
            settlement = period_settlement_summary(instance)
        ret["total_completed_pieces"] = aggregates["total_completed_pieces"] or 0
        ret["total_fixed_salary"] = aggregates["total_fixed_salary"] or Decimal("0.00")
        ret["total_piece_rate_earnings"] = aggregates[
            "total_piece_rate_earnings"
        ] or Decimal("0.00")
        ret["total_gross_salary"] = aggregates["total_gross_salary"] or Decimal("0.00")
        ret["total_attendance_amount"] = aggregates[
            "total_attendance_amount"
        ] or Decimal("0.00")
        ret["total_payable"] = aggregates["total_payable"] or Decimal("0.00")
        ret["entry_count"] = aggregates["entry_count"] or 0
        ret["settlement"] = settlement
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
            "salary_model",
            "fixed_salary_amount",
            "piece_rate_earnings",
            "gross_salary",
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
            "salary_model",
            "fixed_salary_amount",
            "piece_rate_earnings",
            "gross_salary",
            "attendance_amount",
            "total_payable",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["tailor"] = TailorSerializer(instance.tailor, context=self.context).data
        ret["salary_model_display"] = instance.get_salary_model_display()
        if hasattr(instance, "_payments_total"):
            ret["settlement"] = settlement_summary(
                instance,
                precomputed={
                    "advance_deductions": (
                        instance._advance_deductions or Decimal("0.00")
                    ),
                    "payments_recorded": instance._payments_total or Decimal("0.00"),
                    "payment_count": instance._payment_count or 0,
                },
            )
        else:
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
