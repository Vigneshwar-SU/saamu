"""Customer and measurement models for Saamu Tailors.

Business context: customers bring their own cloth and the shop stitches
clothes based on their measurements. A customer returns multiple times, so
measurements are reusable and must retain history.

Measurement units: all numeric measurement fields are stored in **inches**
(decimal values, one decimal place). One unit only for the first version.
"""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Upper sanity bound for any single measurement in inches. A generous limit
# that rejects nonsense values while never interfering with real tailoring.
SENSIBLE_MAX_INCHES = Decimal("300.0")


class GarmentType(models.TextChoices):
    """Garment types supported for tailoring measurements."""

    SHIRT = "SHIRT", "Shirt"
    PANT = "PANT", "Pant"


# Measurement fields available per garment type. These are the only fields the
# API accepts for each garment; mixing garment-specific fields is rejected.
SHIRT_MEASUREMENT_FIELDS = (
    "neck_circumference",
    "chest_circumference",
    "waist_circumference",
    "shoulder_width",
    "sleeve_length",
    "sleeve_circumference",
    "cuff_circumference",
    "shirt_length",
)

PANT_MEASUREMENT_FIELDS = (
    "waist_circumference",
    "hip_circumference",
    "thigh_circumference",
    "knee_circumference",
    "bottom_circumference",
    "length",
)

# Required values per garment type. Optional fields may be omitted.
SHIRT_REQUIRED_FIELDS = (
    "neck_circumference",
    "chest_circumference",
    "waist_circumference",
    "shoulder_width",
    "sleeve_length",
    "shirt_length",
)

PANT_REQUIRED_FIELDS = (
    "waist_circumference",
    "hip_circumference",
    "length",
)

GARMENT_REQUIRED_FIELDS = {
    GarmentType.SHIRT: SHIRT_REQUIRED_FIELDS,
    GarmentType.PANT: PANT_REQUIRED_FIELDS,
}

GARMENT_ALLOWED_FIELDS = {
    GarmentType.SHIRT: SHIRT_MEASUREMENT_FIELDS,
    GarmentType.PANT: PANT_MEASUREMENT_FIELDS,
}

ALL_MEASUREMENT_FIELDS = tuple(
    dict.fromkeys(SHIRT_MEASUREMENT_FIELDS + PANT_MEASUREMENT_FIELDS)
)


class Customer(models.Model):
    """A person who brings cloth to Saamu Tailors for stitching."""

    full_name = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=16)
    alternate_mobile_number = models.CharField(max_length=16, blank=True)
    address = models.TextField(blank=True, max_length=1000)
    notes = models.TextField(blank=True, max_length=2000)
    is_active = models.BooleanField(
        default=True,
        help_text=(
            "Archived customers are marked inactive but are retained so "
            "historical relationships remain intact."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["mobile_number"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.full_name} (#{self.pk})"


def inch_field():
    """A numeric tailoring measurement stored in inches (one decimal place)."""
    return models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.1")),
            MaxValueValidator(SENSIBLE_MAX_INCHES),
        ],
        help_text="Measurement in inches.",
    )


class Measurement(models.Model):
    """A customer's tailoring measurements for a specific garment type.

    History strategy (chosen): immutable records with a current marker.
    Every recorded change creates a NEW row (higher ``version``) and marks it
    current; the previous current row for that (customer, garment_type) is
    unmarked. Existing rows are never mutated in place, so history is always
    preserved and ``is_current`` identifies the applicable measurement.
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="measurements"
    )
    garment_type = models.CharField(max_length=10, choices=GarmentType.choices)
    version = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)
    notes = models.TextField(blank=True, max_length=2000)

    # Shirt measurements (inches)
    neck_circumference = inch_field()
    chest_circumference = inch_field()
    waist_circumference = inch_field()
    shoulder_width = inch_field()
    sleeve_length = inch_field()
    sleeve_circumference = inch_field()
    cuff_circumference = inch_field()
    shirt_length = inch_field()

    # Pant measurements (inches)
    hip_circumference = inch_field()
    thigh_circumference = inch_field()
    knee_circumference = inch_field()
    bottom_circumference = inch_field()
    length = inch_field()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["garment_type", "version"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "garment_type", "version"],
                name="uniq_customer_garment_version",
            )
        ]

    def __str__(self):
        return f"{self.get_garment_type_display()} v{self.version} for {self.customer}"
