"""Salary advances and payroll payments for payroll settlement.

Phase 7 records money movements against finalized payroll without ever
rewriting payroll earnings. ``SalaryAdvance`` tracks money given to a tailor
ahead of payroll; ``PayrollPayment`` records payments made against a finalized
``PayrollEntry``. Both are financial history: they are never physically
deleted, so the record stays visible even after a tailor is archived.

Advances are linked to a payroll entry only through the explicit
``apply-advance`` operation (see ``apps.payments.services``), which flips the
advance to DEDUCTED and records the target entry (``payroll_entry``) and the
moment of deduction. The target entry must belong to a FINALIZED payroll
period, which cannot be recalculated, so the link is never invalidated by a
period recalculation. ``PayrollPayment.tailor`` is always the payroll entry's
tailor; the match is enforced at settlement time, not by a database
constraint (cross-table constraints are not supported by CheckConstraint).
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel
from apps.payroll.models import PayrollEntry, PayrollPeriod
from apps.tailors.models import Tailor


class SalaryAdvance(TimeStampedModel):
    """Money advanced to a tailor before payroll is settled.

    ``status`` starts OUTSTANDING and moves to DEDUCTED only through the
    explicit apply-advance operation, which also records the payroll entry the
    advance was deducted against and the moment of deduction.
    """

    class Status(models.TextChoices):
        OUTSTANDING = "OUTSTANDING", "Outstanding"
        DEDUCTED = "DEDUCTED", "Deducted"

    tailor = models.ForeignKey(
        Tailor,
        on_delete=models.PROTECT,
        related_name="salary_advances",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    advance_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OUTSTANDING
    )
    notes = models.TextField(blank=True, default="")
    payroll_entry = models.ForeignKey(
        PayrollEntry,
        on_delete=models.PROTECT,
        related_name="advance_deductions",
        null=True,
        blank=True,
    )
    deducted_at = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_salary_advances",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-advance_date", "-created_at"]
        verbose_name = "Salary Advance"
        verbose_name_plural = "Salary Advances"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="salary_advance_amount_positive",
            )
        ]
        indexes = [
            models.Index(fields=["tailor", "advance_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.tailor.full_name} - {self.amount} ({self.get_status_display()})"

    def clean(self):
        if self.payroll_entry_id is not None:
            if self.tailor_id != self.payroll_entry.tailor_id:
                raise ValidationError(
                    "An advance can only be deducted against its own tailor's payroll entry."
                )
            if (
                self.payroll_entry.payroll_period.status
                != PayrollPeriod.Status.FINALIZED
            ):
                raise ValidationError(
                    "Advances can only be deducted against finalized payroll periods."
                )


class PayrollPayment(TimeStampedModel):
    """A payment recorded against a finalized payroll entry."""

    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
        UPI = "UPI", "UPI"
        OTHER = "OTHER", "Other"

    payroll_entry = models.ForeignKey(
        PayrollEntry,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    tailor = models.ForeignKey(
        Tailor,
        on_delete=models.PROTECT,
        related_name="payroll_payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_payroll_payments",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        verbose_name = "Payroll Payment"
        verbose_name_plural = "Payroll Payments"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="payroll_payment_amount_positive",
            )
        ]
        indexes = [
            models.Index(fields=["payroll_entry", "payment_date"]),
            models.Index(fields=["tailor", "payment_date"]),
        ]

    def __str__(self):
        return (
            f"{self.tailor.full_name} - {self.amount} "
            f"({self.get_payment_method_display()})"
        )
