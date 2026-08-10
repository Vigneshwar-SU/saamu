"""Serializers for customers and measurements.

All numeric measurement values are validated on the backend: supported
garment type, valid customer reference, sensible ranges (0.1 - 300.0 inches),
per-garment required fields, and field-length limits. Frontend validation is
never treated as a security boundary.
"""

import re

from django.db import transaction
from django.db.models import Max
from rest_framework import serializers

from apps.customers.models import (
    ALL_MEASUREMENT_FIELDS,
    GARMENT_ALLOWED_FIELDS,
    GARMENT_REQUIRED_FIELDS,
    Customer,
    GarmentType,
    Measurement,
)

MOBILE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")
_PHONE_FORMATTING_RE = re.compile(r"[\s\-()./]+")
_INDIA_COUNTRY_CODE = "91"
_INDIA_MOBILE_PREFIXES = ("6", "7", "8", "9")

MAX_NAME_LENGTH = 200
MAX_MOBILE_LENGTH = 16
MAX_ADDRESS_LENGTH = 1000
MAX_NOTES_LENGTH = 2000


def normalize_mobile_number(value):
    """Return a digit-only lookup key for a mobile number, or ``None``.

    Mirrors the billing app's WhatsApp normalization so ``9876543210``,
    ``+919876543210`` and ``0 98765 43210`` are recognized as the same number.
    Unusable values return ``None`` and are skipped by duplicate checks.
    """
    if value is None:
        return None
    cleaned = _PHONE_FORMATTING_RE.sub("", str(value).strip())
    if not cleaned:
        return None
    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if digits.isdigit() and 7 <= len(digits) <= 15:
            return digits
        return None
    if cleaned.isdigit():
        if len(cleaned) == 10 and cleaned[0] in _INDIA_MOBILE_PREFIXES:
            return _INDIA_COUNTRY_CODE + cleaned
        if (
            len(cleaned) == 11
            and cleaned[0] == "0"
            and cleaned[1] in _INDIA_MOBILE_PREFIXES
        ):
            return _INDIA_COUNTRY_CODE + cleaned[1:]
    return None


class CustomerSerializer(serializers.ModelSerializer):
    """Public representation of a customer.

    ``is_active`` is read-only through the update serializer: deactivation is
    performed only through the dedicated archive/restore actions so it is
    always an explicit, intentional operation.
    """

    class Meta:
        model = Customer
        fields = (
            "id",
            "full_name",
            "mobile_number",
            "alternate_mobile_number",
            "address",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "is_active", "created_at", "updated_at")
        extra_kwargs = {
            "full_name": {"max_length": MAX_NAME_LENGTH},
            "mobile_number": {"max_length": MAX_MOBILE_LENGTH},
            "alternate_mobile_number": {
                "max_length": MAX_MOBILE_LENGTH,
                "allow_blank": True,
                "required": False,
            },
            "address": {
                "max_length": MAX_ADDRESS_LENGTH,
                "allow_blank": True,
                "required": False,
                "trim_whitespace": False,
            },
            "notes": {
                "max_length": MAX_NOTES_LENGTH,
                "allow_blank": True,
                "required": False,
                "trim_whitespace": False,
            },
        }

    def validate_full_name(self, value):
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError(
                "Full name must contain at least one letter."
            )
        return value

    def validate_mobile_number(self, value):
        value = (value or "").strip()
        if not MOBILE_REGEX.match(value):
            raise serializers.ValidationError(
                "Enter a valid mobile number (10-15 digits, optional leading +)."
            )
        return value

    def validate_alternate_mobile_number(self, value):
        if not value:
            return value
        value = value.strip()
        if not MOBILE_REGEX.match(value):
            raise serializers.ValidationError(
                "Enter a valid mobile number (10-15 digits, optional leading +)."
            )
        return value

    def validate(self, attrs):
        primary = attrs.get("mobile_number")
        alternate = attrs.get("alternate_mobile_number")

        primary_key = normalize_mobile_number(primary)
        alternate_key = normalize_mobile_number(alternate)

        instance = self.instance
        current_primary = (
            normalize_mobile_number(instance.mobile_number) if instance else None
        )
        current_alternate = (
            normalize_mobile_number(instance.alternate_mobile_number)
            if instance
            else None
        )

        if primary_key and alternate_key and primary_key == alternate_key:
            raise serializers.ValidationError(
                {
                    "alternate_mobile_number": "Alternate mobile must differ from the primary mobile."
                }
            )
        if instance is not None:
            if primary_key and current_alternate and primary_key == current_alternate:
                raise serializers.ValidationError(
                    {
                        "mobile_number": "Primary mobile must differ from the alternate mobile."
                    }
                )
            if alternate_key and current_primary and alternate_key == current_primary:
                raise serializers.ValidationError(
                    {
                        "alternate_mobile_number": "Alternate mobile must differ from the primary mobile."
                    }
                )

        # A value that is unchanged from the record's own current value is not
        # a new duplicate: pre-existing duplicate rows remain editable (e.g. to
        # fix their name) without being locked out.
        if primary_key == current_primary:
            primary_key = None
        if alternate_key == current_alternate:
            alternate_key = None

        if not primary_key and not alternate_key:
            return attrs

        existing = Customer.objects.values_list(
            "pk", "mobile_number", "alternate_mobile_number"
        )
        if instance is not None:
            existing = existing.exclude(pk=instance.pk)

        for pk, other_primary, other_alternate in existing:
            other_keys = {
                normalize_mobile_number(other_primary),
                normalize_mobile_number(other_alternate),
            }
            if primary_key and primary_key in other_keys:
                raise serializers.ValidationError(
                    {
                        "mobile_number": "A customer with this mobile number already exists."
                    }
                )
            if alternate_key and alternate_key in other_keys:
                raise serializers.ValidationError(
                    {
                        "alternate_mobile_number": "A customer with this alternate mobile number already exists."
                    }
                )
        return attrs


class MeasurementSerializer(serializers.ModelSerializer):
    """Measurement serializer.

    ``customer``, ``version`` and ``is_current`` are read-only and managed by
    the API: the nested customer route supplies the customer, and creating a
    measurement always produces the next version and marks it current.
    """

    class Meta:
        model = Measurement
        fields = (
            "id",
            "customer",
            "garment_type",
            "version",
            "is_current",
            "notes",
            *ALL_MEASUREMENT_FIELDS,
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "customer",
            "version",
            "is_current",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "notes": {
                "max_length": MAX_NOTES_LENGTH,
                "allow_blank": True,
                "required": False,
                "trim_whitespace": False,
            },
        }

    def validate(self, attrs):
        garment_type = attrs.get("garment_type")

        if garment_type not in GarmentType.values:
            raise serializers.ValidationError(
                {"garment_type": "Unsupported garment type. Supported: SHIRT, PANT."}
            )

        allowed = GARMENT_ALLOWED_FIELDS[garment_type]
        required = GARMENT_REQUIRED_FIELDS[garment_type]

        # Reject fields that do not belong to this garment type.
        for field_name in attrs:
            if field_name in ALL_MEASUREMENT_FIELDS and field_name not in allowed:
                raise serializers.ValidationError(
                    {
                        field_name: f"'{field_name}' is not a valid field for "
                        f"{GarmentType(garment_type).label}."
                    }
                )

        # Require the mandatory values for this garment type.
        label = GarmentType(garment_type).label
        for field_name in required:
            if attrs.get(field_name) is None:
                raise serializers.ValidationError(
                    {field_name: f"This field is required for {label}."}
                )

        return attrs

    def create(self, validated_data):
        """Create the next immutable version and mark it as the current one."""
        customer = validated_data["customer"]
        garment_type = validated_data["garment_type"]

        with transaction.atomic():
            max_version = (
                Measurement.objects.filter(
                    customer=customer, garment_type=garment_type
                ).aggregate(max=Max("version"))["max"]
                or 0
            )
            Measurement.objects.filter(
                customer=customer, garment_type=garment_type, is_current=True
            ).update(is_current=False)
            validated_data["version"] = max_version + 1
            validated_data["is_current"] = True
            return Measurement.objects.create(**validated_data)
