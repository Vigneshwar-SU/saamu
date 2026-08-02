"""Serializers for tailors, piece rates and work assignments."""

import re

from rest_framework import serializers

from apps.customers.serializers import (
    MAX_MOBILE_LENGTH,
    MAX_NAME_LENGTH,
    MAX_NOTES_LENGTH,
)
from apps.orders.models import Order, OrderItem

from .models import PieceRate, Tailor, WorkAssignment

MOBILE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")


class TailorSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="full_name", max_length=MAX_NAME_LENGTH)
    mobile_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
        max_length=MAX_MOBILE_LENGTH,
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
        max_length=MAX_NOTES_LENGTH,
    )
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = Tailor
        fields = [
            "id",
            "name",
            "mobile_number",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_mobile_number(self, value):
        value = (value or "").strip()
        if value and not MOBILE_REGEX.match(value):
            raise serializers.ValidationError("Enter a valid mobile number.")
        return value


class PieceRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PieceRate
        fields = [
            "id",
            "garment_type",
            "rate_per_piece",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "rate_per_piece": {"max_digits": 12, "decimal_places": 2},
        }

    def validate_garment_type(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Garment type is required.")
        return value


class WorkAssignmentSerializer(serializers.ModelSerializer):
    tailor = serializers.PrimaryKeyRelatedField(queryset=Tailor.objects.all())
    order_item = serializers.PrimaryKeyRelatedField(queryset=OrderItem.objects.all())
    status = serializers.ChoiceField(choices=WorkAssignment.Status.choices)
    rate_per_piece_snapshot = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    earned_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    remaining_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = WorkAssignment
        fields = [
            "id",
            "tailor",
            "order_item",
            "assigned_quantity",
            "completed_quantity",
            "remaining_quantity",
            "status",
            "rate_per_piece_snapshot",
            "earned_amount",
            "assigned_at",
            "started_at",
            "completed_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "assigned_at",
            "started_at",
            "completed_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "assigned_quantity": {"min_value": 1},
            "completed_quantity": {"min_value": 0},
        }

    def validate_tailor(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Assignments can only be created for active tailors."
            )
        return value

    def validate_order_item(self, value):
        order_item = value
        if (
            not order_item
            or not hasattr(order_item, "order")
            or order_item.order is None
        ):
            raise serializers.ValidationError("Invalid order item.")
        return value

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["tailor"] = TailorSerializer(instance.tailor, context=self.context).data
        ret["order_item"] = self._order_item_representation(instance.order_item)
        return ret

    def _order_item_representation(self, order_item):
        return {
            "id": order_item.pk,
            "garment_type": order_item.get_garment_type_display(),
            "garment_code": order_item.garment_type,
            "quantity": order_item.quantity,
            "order": order_item.order_id,
            "order_number": order_item.order.order_number,
            "order_status": order_item.order.status,
            "customer": order_item.order.customer_id,
            "customer_name": order_item.order.customer.full_name,
        }


class WorkAssignmentCreateSerializer(WorkAssignmentSerializer):
    status = serializers.HiddenField(default=WorkAssignment.Status.ASSIGNED)
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    class Meta(WorkAssignmentSerializer.Meta):
        fields = WorkAssignmentSerializer.Meta.fields + ["order"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        order_item = attrs["order_item"]
        order = attrs["order"]
        if order_item.order_id != order.id:
            raise serializers.ValidationError(
                {
                    "order_item": "The selected order item does not belong to the chosen order."
                }
            )
        return attrs
