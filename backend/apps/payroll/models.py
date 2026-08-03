"""Payroll periods and per-tailor payroll entries.

Payroll is piece-rate only: each completed ``WorkAssignment`` contributes
``completed_quantity * rate_per_piece_snapshot`` (the immutable snapshot, never
the current PieceRate). Outstanding or in-progress pieces contribute zero.

Payroll periods follow ``DRAFT -> CALCULATED -> FINALIZED``. Only
``calculate()`` writes entries; a FINALIZED period rejects recalculation.
Payroll records are never physically deleted, so historical payroll remains
available even after a tailor is archived.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.attendance.models import Attendance
from apps.common.models import TimeStampedModel
from apps.tailors.models import Tailor, WorkAssignment


class PayrollPeriod(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CALCULATED = "CALCULATED", "Calculated"
        FINALIZED = "FINALIZED", "Finalized"

    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_payroll_periods",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-period_start", "-id"]
        verbose_name = "Payroll Period"
        verbose_name_plural = "Payroll Periods"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(period_start__lte=models.F("period_end")),
                name="payroll_period_start_before_end",
            )
        ]
        indexes = [
            models.Index(fields=["period_start", "period_end"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.period_start} to {self.period_end} ({self.get_status_display()})"

    def completed_assignments(self):
        """Completed assignments whose completion date falls in this period.

        Inclusion is driven by the assignment completion timestamp
        (``completed_at``), never by order dates. Boundaries are inclusive:
        ``period_start <= completion_date <= period_end``.
        """
        return WorkAssignment.objects.filter(
            status=WorkAssignment.Status.COMPLETED,
            completed_at__date__gte=self.period_start,
            completed_at__date__lte=self.period_end,
        )

    def calculate(self):
        """Aggregate piece-rate earnings and attendance for the period.

        Creates one ``PayrollEntry`` per tailor with any completed work or any
        attendance record inside the period. Missing attendance is never
        treated as PRESENT. Attendance currently carries no configured
        monetary value, so ``attendance_amount`` stays zero and
        ``total_payable == piece_rate_earnings``.

        Replaces all previous entries, so a CALCULATED period can be
        recalculated while editable. FINALIZED periods are immutable and raise.
        """
        if self.status == self.Status.FINALIZED:
            raise ValidationError("Finalized payroll periods cannot be recalculated.")

        with transaction.atomic():
            self.entries.all().delete()

            pieces_by_tailor = {}
            earnings_by_tailor = {}
            for assignment in self.completed_assignments().select_related("tailor"):
                tailor_id = assignment.tailor_id
                pieces_by_tailor[tailor_id] = (
                    pieces_by_tailor.get(tailor_id, 0) + assignment.completed_quantity
                )
                earned = (
                    assignment.completed_quantity * assignment.rate_per_piece_snapshot
                )
                earnings_by_tailor[tailor_id] = (
                    earnings_by_tailor.get(tailor_id, Decimal("0.00")) + earned
                )

            attendance_by_tailor = {}
            attendance_qs = Attendance.objects.filter(
                attendance_date__gte=self.period_start,
                attendance_date__lte=self.period_end,
            )
            for record in attendance_qs:
                entry = attendance_by_tailor.setdefault(
                    record.tailor_id, {"present": 0, "half": 0, "absent": 0}
                )
                if record.status == Attendance.Status.PRESENT:
                    entry["present"] += 1
                elif record.status == Attendance.Status.HALF_DAY:
                    entry["half"] += 1
                elif record.status == Attendance.Status.ABSENT:
                    entry["absent"] += 1

            tailor_ids = (
                set(pieces_by_tailor)
                | set(earnings_by_tailor)
                | set(attendance_by_tailor)
            )
            entries = []
            for tailor_id in tailor_ids:
                attendance = attendance_by_tailor.get(
                    tailor_id, {"present": 0, "half": 0, "absent": 0}
                )
                piece_rate_earnings = earnings_by_tailor.get(tailor_id, Decimal("0.00"))
                attendance_amount = Decimal("0.00")
                entries.append(
                    PayrollEntry(
                        payroll_period=self,
                        tailor_id=tailor_id,
                        present_days=attendance["present"],
                        half_days=attendance["half"],
                        absent_days=attendance["absent"],
                        completed_pieces=pieces_by_tailor.get(tailor_id, 0),
                        piece_rate_earnings=piece_rate_earnings,
                        attendance_amount=attendance_amount,
                        total_payable=piece_rate_earnings + attendance_amount,
                    )
                )
            PayrollEntry.objects.bulk_create(entries)

            self.status = self.Status.CALCULATED
            self.save(update_fields=["status", "updated_at"])
        return entries


class PayrollEntry(TimeStampedModel):
    """Per-tailor summary row for one payroll period.

    ``piece_rate_earnings`` is the sum of ``completed_quantity *
    rate_per_piece_snapshot`` across completed assignments inside the period.
    ``attendance_amount`` has no configured rule in Phase 6 and remains zero.
    """

    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    tailor = models.ForeignKey(
        Tailor,
        on_delete=models.PROTECT,
        related_name="payroll_entries",
    )
    present_days = models.PositiveIntegerField(default=0)
    half_days = models.PositiveIntegerField(default=0)
    absent_days = models.PositiveIntegerField(default=0)
    completed_pieces = models.PositiveIntegerField(default=0)
    piece_rate_earnings = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    attendance_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    total_payable = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        ordering = ["tailor__full_name", "id"]
        verbose_name = "Payroll Entry"
        verbose_name_plural = "Payroll Entries"
        constraints = [
            models.UniqueConstraint(
                fields=["payroll_period", "tailor"],
                name="unique_payroll_entry_per_period_tailor",
            )
        ]
        indexes = [
            models.Index(fields=["payroll_period", "tailor"]),
        ]

    def __str__(self):
        return f"{self.tailor.full_name} - {self.payroll_period}"
