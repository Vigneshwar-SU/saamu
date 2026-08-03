"""Serializers for income and expense records."""

from decimal import Decimal

from rest_framework import serializers

from .models import Expense, Income


class IncomeSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Income
        fields = [
            "id",
            "category",
            "category_display",
            "amount",
            "income_date",
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
                "Income amount must be greater than zero."
            )
        return value


class ExpenseSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
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
