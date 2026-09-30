"""Order, order item and status history models for Saamu Tailors.

Business context: a customer brings cloth and places an order for one or more
garments (SHIRT / PANT). Each garment item records the exact measurement state
that was used when the order was created (an immutable snapshot), so later
changes to the customer's measurement chart never alter historical orders.

Deletion policy: orders are never physically deleted. They progress through a
controlled status lifecycle and can only be cancelled (terminal).

Shirt variants (Full Shirt / Half Shirt):
A SHIRT can be cut as a Full Shirt or a Half Shirt. The two share ONE set of
body measurements, so ``Measurement`` is deliberately left untouched: both
variants continue to reference the customer's ``SHIRT`` measurement row. The
difference lives entirely on the order line (pricing) and on the tailor work
that follows it (piece rates), both of which are keyed off
``OrderItem.piece_rate_key``.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.authentication.models import User
from apps.customers.models import (
    GARMENT_ALLOWED_FIELDS,
    GARMENT_REQUIRED_FIELDS,
    Customer,
    GarmentType,
    Measurement,
)


class ShirtType(models.TextChoices):
    """Shirt cut variants.

    Both variants use the SAME ``SHIRT`` measurement; the choice only affects
    pricing and tailor work, never the measurement chart.
    """

    FULL = "FULL", "Full Shirt"
    HALF = "HALF", "Half Shirt"


# Tailor piece rates are configured per garment variant, stored as
# ``PieceRate.garment_type`` values (a free-form, unique key on that model, so
# no competing rate system is introduced). PANT keys stay on the plain garment
# code; shirt variants get their own key so a tailor can be paid differently for
# a Full Shirt than for a Half Shirt.
PIECE_RATE_KEY_FULL_SHIRT = "SHIRT_FULL"
PIECE_RATE_KEY_HALF_SHIRT = "SHIRT_HALF"


def garment_label(garment_type, shirt_type=None):
    """Canonical display label for an order line.

    Returns "Full Shirt" / "Half Shirt" for a shirt variant, "Pant" for a pant,
    and falls back to the plain garment label ("Shirt") for legacy shirt lines
    recorded before variants existed, so historical data is never silently
    reclassified as a Full Shirt.
    """
    if garment_type == GarmentType.SHIRT and shirt_type == ShirtType.FULL:
        return ShirtType.FULL.label
    if garment_type == GarmentType.SHIRT and shirt_type == ShirtType.HALF:
        return ShirtType.HALF.label
    if garment_type == GarmentType.PANT:
        return GarmentType.PANT.label
    return GarmentType(garment_type).label if garment_type in GarmentType.values else ""


def piece_rate_key(garment_type, shirt_type=None):
    """Tailor piece-rate configuration key for an order line.

    Shirt variants resolve to their own configurable key so Full Shirt and Half
    Shirt can carry different tailor rates; legacy shirt lines (no variant
    recorded) keep resolving to the plain ``SHIRT`` rate that already exists, so
    historical assignments and payroll are unaffected.
    """
    if garment_type == GarmentType.SHIRT:
        if shirt_type == ShirtType.FULL:
            return PIECE_RATE_KEY_FULL_SHIRT
        if shirt_type == ShirtType.HALF:
            return PIECE_RATE_KEY_HALF_SHIRT
    return garment_type


class OrderStatus(models.TextChoices):
    """Order status lifecycle.

    COLLECTED and CANCELLED are terminal states.
    """

    NEW = "NEW", "New"
    CUTTING = "CUTTING", "Cutting"
    STITCHING = "STITCHING", "Stitching"
    READY = "READY", "Ready"
    COLLECTED = "COLLECTED", "Collected"
    CANCELLED = "CANCELLED", "Cancelled"


# Allowed forward transitions. Any transition not listed here (or leaving a
# terminal state) is rejected by the API.
ALLOWED_TRANSITIONS = {
    OrderStatus.NEW: {OrderStatus.CUTTING, OrderStatus.CANCELLED},
    OrderStatus.CUTTING: {OrderStatus.STITCHING, OrderStatus.CANCELLED},
    OrderStatus.STITCHING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.COLLECTED, OrderStatus.CANCELLED},
    OrderStatus.COLLECTED: set(),
    OrderStatus.CANCELLED: set(),
}

TERMINAL_STATUSES = {OrderStatus.COLLECTED, OrderStatus.CANCELLED}

MAX_PRICE_DIGITS = 10
MAX_PRICE_DECIMALS = 2


class Order(models.Model):
    """A tailoring order placed by an existing customer."""

    order_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Human-friendly unique order number, e.g. ORD-2026-0001.",
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    order_date = models.DateField(
        default=timezone.localdate,
        help_text="Date the order was received / cloth accepted.",
    )
    expected_delivery_date = models.DateField(
        null=True, blank=True, help_text="Optional expected delivery date."
    )
    status = models.CharField(
        max_length=12,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
    )
    notes = models.TextField(blank=True, max_length=4000)
    total_amount = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=MAX_PRICE_DECIMALS,
        default=Decimal("0.00"),
        help_text="Sum of all line item amounts. Never floating-point.",
    )
    collected_at = models.DateTimeField(
        null=True, blank=True, help_text="Set when the order becomes COLLECTED."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["order_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["customer", "order_date"]),
        ]

    def __str__(self):
        return f"{self.order_number} ({self.get_status_display()})"

    def _generate_order_number(self):
        """Create the next human-friendly order number for the current year.

        Format: ``ORD-YYYY-NNNN``. Numbers are zero-padded to four digits so
        lexicographic ordering matches numeric ordering. The database unique
        constraint on ``order_number`` is the final guard against duplicates.
        """
        year = timezone.localdate().year
        prefix = f"ORD-{year}-"
        last = (
            Order.objects.filter(order_number__startswith=prefix)
            .order_by("-order_number")
            .values_list("order_number", flat=True)
            .first()
        )
        if last is None:
            sequence = 1
        else:
            try:
                sequence = int(last.rsplit("-", 1)[1]) + 1
            except (ValueError, IndexError):
                sequence = 1
        return f"{prefix}{sequence:04d}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @property
    def is_terminal(self):
        return self.status in TERMINAL_STATUSES


class OrderItem(models.Model):
    """A single garment line on an order.

    The measurement used for the garment is preserved twice:
    - ``measurement`` -> direct reference to the exact Measurement row/version.
    - ``measurement_snapshot`` -> immutable JSON of the values at order time.

    The snapshot guarantees historical correctness even if the referenced
    measurement is ever changed or removed. Measurement history rows are never
    mutated in place (Phase 3), so the reference is stable in practice.

    Shirt variants: ``shirt_type`` records Full Shirt / Half Shirt for SHIRT
    lines and stays NULL for PANT. Both shirt variants keep referencing the
    customer's SHIRT ``Measurement`` row -- measurements are never duplicated.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    garment_type = models.CharField(max_length=10, choices=GarmentType.choices)
    shirt_type = models.CharField(
        max_length=4,
        choices=ShirtType.choices,
        null=True,
        blank=True,
        help_text=(
            "Shirt cut variant. Required for SHIRT items, always NULL for PANT. "
            "NULL is tolerated at the database level so pre-existing shirt lines "
            "are never silently reclassified."
        ),
    )
    quantity = models.PositiveIntegerField(default=1)
    measurement = models.ForeignKey(
        Measurement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        help_text="Reference to the exact measurement version used at order time.",
    )
    measurement_version = models.PositiveIntegerField(
        null=True, blank=True, help_text="Measurement version used when ordering."
    )
    measurement_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Immutable copy of the measurement values used for this item.",
    )
    unit_price = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=MAX_PRICE_DECIMALS,
        default=Decimal("0.00"),
        help_text="Per-piece price in INR.",
    )
    notes = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["order", "garment_type"]),
        ]
        constraints = [
            # A shirt variant is meaningless on a pant, and a pant must never
            # carry one. Legacy SHIRT rows with a NULL variant still satisfy
            # this constraint, so the rule is safe to add over existing data.
            models.CheckConstraint(
                condition=(
                    models.Q(garment_type=GarmentType.PANT, shirt_type__isnull=True)
                    | models.Q(garment_type=GarmentType.SHIRT)
                ),
                name="orderitem_shirt_type_only_on_shirt",
            ),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.garment_label} on {self.order}"

    @property
    def garment_label(self):
        """Display label distinguishing Full Shirt / Half Shirt / Pant."""
        return garment_label(self.garment_type, self.shirt_type)

    @property
    def piece_rate_key(self):
        """Configurable tailor piece-rate key for this line.

        Resolves Full Shirt and Half Shirt to separate rate keys so the two can
        be paid differently, while legacy shirt lines keep resolving to the
        existing plain ``SHIRT`` rate and historical payroll stays untouched.
        """
        return piece_rate_key(self.garment_type, self.shirt_type)

    @property
    def amount(self):
        """Line total (quantity * unit_price), always computed, never stored."""
        return self.unit_price * self.quantity

    def clean(self):
        """Enforce the shirt-variant rule at the model layer.

        SHIRT lines must declare Full or Half; PANT lines must not declare a
        variant. Runs in addition to (never instead of) serializer validation.
        """
        super().clean()
        if self.garment_type == GarmentType.SHIRT:
            if not self.shirt_type:
                raise ValidationError(
                    {
                        "shirt_type": (
                            "Select Full Shirt or Half Shirt for a Shirt item. "
                            "Both variants use the customer's existing Shirt "
                            "measurements."
                        )
                    }
                )
        elif self.garment_type == GarmentType.PANT and self.shirt_type:
            raise ValidationError(
                {"shirt_type": "Shirt Type is not applicable to a Pant."}
            )

    def build_snapshot(self):
        """Return the garment-specific measurement values as plain data.

        Snapshot stores only the fields that belong to this garment type, as
        numeric values, so it is self-contained and immune to later changes.
        """
        if self.measurement is None:
            return None
        allowed = GARMENT_ALLOWED_FIELDS[self.garment_type]
        snapshot = {}
        for field_name in allowed:
            value = getattr(self.measurement, field_name, None)
            snapshot[field_name] = float(value) if value is not None else None
        return snapshot


class OrderStatusHistory(models.Model):
    """Audit trail of order status transitions.

    The initial NEW status is recorded on creation (from_status = None).
    Entries are never mutated or deleted; every transition appends a row.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_history"
    )
    from_status = models.CharField(
        max_length=12,
        choices=OrderStatus.choices,
        null=True,
        blank=True,
        help_text="None for the initial NEW entry.",
    )
    to_status = models.CharField(max_length=12, choices=OrderStatus.choices)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changes",
        help_text="STAFF user who performed the transition.",
    )
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["changed_at", "id"]
        indexes = [
            models.Index(fields=["order", "changed_at"]),
        ]

    def __str__(self):
        source = self.from_status or "-"
        return f"{self.order.order_number}: {source} -> {self.to_status}"
