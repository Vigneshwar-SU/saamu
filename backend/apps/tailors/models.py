from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction

from apps.common.models import TimeStampedModel, now


class Tailor(TimeStampedModel):
    full_name = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=16, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tailor"
        verbose_name_plural = "Tailors"

    def __str__(self):
        return self.full_name


class PieceRate(TimeStampedModel):
    garment_type = models.CharField(max_length=50, unique=True)
    rate_per_piece = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["garment_type"]
        verbose_name = "Piece Rate"
        verbose_name_plural = "Piece Rates"

    def __str__(self):
        return f"{self.garment_type}: {self.rate_per_piece}"


class WorkAssignment(TimeStampedModel):
    class Status(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    ALLOWED_TRANSITIONS = {
        Status.ASSIGNED: {Status.IN_PROGRESS},
        Status.IN_PROGRESS: {Status.COMPLETED},
    }

    tailor = models.ForeignKey(
        Tailor,
        on_delete=models.PROTECT,
        related_name="work_assignments",
    )
    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.PROTECT,
        related_name="work_assignments",
    )
    assigned_quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    completed_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ASSIGNED
    )
    rate_per_piece_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_work_assignments",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-assigned_at"]
        verbose_name = "Work Assignment"
        verbose_name_plural = "Work Assignments"

    def __str__(self):
        return f"{self.tailor.full_name} - {self.order_item} ({self.status})"

    @property
    def earned_amount(self):
        return self.completed_quantity * self.rate_per_piece_snapshot

    @property
    def remaining_quantity(self):
        return self.assigned_quantity - self.completed_quantity

    def advance_status(self, to_status):
        allowed = self.ALLOWED_TRANSITIONS.get(self.Status(self.status), set())
        if to_status not in allowed:
            return False
        with transaction.atomic():
            self.status = to_status
            if to_status == self.Status.IN_PROGRESS and self.started_at is None:
                self.started_at = now()
            if to_status == self.Status.COMPLETED:
                self.completed_at = now()
            self.save(
                update_fields=[
                    "status",
                    "completed_quantity",
                    "started_at",
                    "completed_at",
                    "updated_at",
                ]
            )
        return True
