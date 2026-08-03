"""Payroll periods, per-tailor payroll entries and salary configurations.

Payroll follows each tailor's effective ``TailorSalaryConfiguration``
(``PER_GARMENT`` / ``FIXED_SALARY`` / ``MIXED``). Every completed
``WorkAssignment`` contributes ``completed_quantity * rate_per_piece_snapshot``
(the immutable snapshot, never the current PieceRate); outstanding or
in-progress pieces contribute zero. A FIXED or MIXED tailor adds the configured
fixed salary for the period. The configuration in effect at the period start is
snapshotted onto each ``PayrollEntry``, so later configuration edits never
rewrite already-calculated payroll.

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


class TailorSalaryConfiguration(TimeStampedModel):
    """How a tailor's salary is computed for payroll periods.

    Three salary models:
    - ``PER_GARMENT``: earnings are piece-rate only (completed pieces x the
      immutable per-assignment rate snapshot). No fixed component.
    - ``FIXED_SALARY``: the tailor is paid a fixed amount for the period.
    - ``MIXED``: a fixed amount plus piece-rate earnings.

    ``effective_from`` / ``effective_to`` define when a configuration applies.
    A payroll period resolves the configuration in effect at its start and
    snapshots the model + fixed amount onto each ``PayrollEntry``, so later
    configuration changes never rewrite already-calculated payroll.
    """

    class SalaryModel(models.TextChoices):
        PER_GARMENT = "PER_GARMENT", "Per Garment"
        FIXED_SALARY = "FIXED_SALARY", "Fixed Salary"
        MIXED = "MIXED", "Fixed + Per Garment"

    tailor = models.ForeignKey(
        Tailor,
        on_delete=models.CASCADE,
        related_name="salary_configurations",
    )
    salary_model = models.CharField(
        max_length=20,
        choices=SalaryModel.choices,
        default=SalaryModel.PER_GARMENT,
    )
    fixed_salary_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_salary_configurations",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["tailor__full_name", "-effective_from", "-id"]
        verbose_name = "Tailor Salary Configuration"
        verbose_name_plural = "Tailor Salary Configurations"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fixed_salary_amount__gte=0),
                name="salary_config_fixed_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(effective_to__isnull=True)
                | models.Q(effective_to__gte=models.F("effective_from")),
                name="salary_config_effective_dates_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["tailor", "effective_from"]),
            models.Index(fields=["salary_model"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.tailor.full_name} - {self.get_salary_model_display()}"


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

    def effective_salary_configuration(self, tailor_id):
        """Active salary configuration in effect at the start of this period.

        A configuration applies when ``effective_from <= period_start`` and it
        is either open-ended or its ``effective_to >= period_start``. The most
        recently started configuration wins. Tailors without a matching active
        configuration are paid per garment (the Phase 6 default).
        """
        return (
            TailorSalaryConfiguration.objects.filter(
                tailor_id=tailor_id,
                is_active=True,
                effective_from__lte=self.period_start,
            )
            .filter(
                models.Q(effective_to__isnull=True)
                | models.Q(effective_to__gte=self.period_start)
            )
            .order_by("-effective_from", "-id")
            .first()
        )

    def calculate(self):
        """Aggregate salary, piece-rate earnings and attendance for the period.

        Creates one ``PayrollEntry`` per tailor with any completed work or any
        attendance record inside the period. For each tailor the active salary
        configuration in effect at ``period_start`` is resolved and snapshotted
        onto the entry: ``PER_GARMENT`` earns only piece rate, ``FIXED_SALARY``
        earns the configured fixed amount, and ``MIXED`` earns fixed + piece
        rate. ``gross_salary = fixed_salary_amount + piece_rate_earnings``.
        Missing attendance is never treated as PRESENT. Attendance currently
        carries no configured monetary value, so ``attendance_amount`` stays
        zero and ``total_payable == gross_salary``.

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
            configs_by_tailor = {}
            for config in (
                TailorSalaryConfiguration.objects.filter(
                    tailor_id__in=tailor_ids,
                    is_active=True,
                    effective_from__lte=self.period_start,
                )
                .filter(
                    models.Q(effective_to__isnull=True)
                    | models.Q(effective_to__gte=self.period_start)
                )
                .order_by("tailor_id", "-effective_from", "-id")
            ):
                configs_by_tailor.setdefault(config.tailor_id, config)

            entries = []
            for tailor_id in tailor_ids:
                attendance = attendance_by_tailor.get(
                    tailor_id, {"present": 0, "half": 0, "absent": 0}
                )
                config = configs_by_tailor.get(tailor_id)
                salary_model = (
                    config.salary_model
                    if config
                    else TailorSalaryConfiguration.SalaryModel.PER_GARMENT
                )
                fixed_salary_amount = (
                    config.fixed_salary_amount
                    if config
                    and config.salary_model
                    != TailorSalaryConfiguration.SalaryModel.PER_GARMENT
                    else Decimal("0.00")
                )
                piece_rate_earnings = (
                    Decimal("0.00")
                    if salary_model
                    == TailorSalaryConfiguration.SalaryModel.FIXED_SALARY
                    else earnings_by_tailor.get(tailor_id, Decimal("0.00"))
                )
                gross_salary = fixed_salary_amount + piece_rate_earnings
                attendance_amount = Decimal("0.00")
                entries.append(
                    PayrollEntry(
                        payroll_period=self,
                        tailor_id=tailor_id,
                        present_days=attendance["present"],
                        half_days=attendance["half"],
                        absent_days=attendance["absent"],
                        completed_pieces=pieces_by_tailor.get(tailor_id, 0),
                        salary_model=salary_model,
                        fixed_salary_amount=fixed_salary_amount,
                        piece_rate_earnings=piece_rate_earnings,
                        gross_salary=gross_salary,
                        attendance_amount=attendance_amount,
                        total_payable=gross_salary + attendance_amount,
                    )
                )
            PayrollEntry.objects.bulk_create(entries)

            self.status = self.Status.CALCULATED
            self.save(update_fields=["status", "updated_at"])
        return entries


class PayrollEntry(TimeStampedModel):
    """Per-tailor summary row for one payroll period.

    ``salary_model`` and ``fixed_salary_amount`` are snapshots of the
    ``TailorSalaryConfiguration`` that was in effect at ``period_start`` when
    the entry was calculated, so historical payroll is reproducible even after
    configuration edits. ``piece_rate_earnings`` is the sum of
    ``completed_quantity * rate_per_piece_snapshot`` across completed
    assignments inside the period. ``gross_salary = fixed_salary_amount +
    piece_rate_earnings``; ``attendance_amount`` has no configured rule in
    Phase 6/10 and remains zero, so ``total_payable == gross_salary``.
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
    salary_model = models.CharField(
        max_length=20,
        choices=TailorSalaryConfiguration.SalaryModel.choices,
        default=TailorSalaryConfiguration.SalaryModel.PER_GARMENT,
    )
    fixed_salary_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    piece_rate_earnings = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    gross_salary = models.DecimalField(
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
