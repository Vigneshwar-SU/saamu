"""Income and expense records for the shop ledger.

Phase 8 records money the shop receives (``Income``) and spends (``Expense``)
against controlled categories. Both are financial history: they are never
physically deleted and carry no update/delete API, so the ledger stays intact
even after the recorder is gone. ``recorded_by`` is always set server-side from
the authenticated user and never accepted from a client.

The ledger is deliberately separate from payroll: payroll settlements live in
``apps.payments`` (``PayrollPayment``) and salary advances stay a distinct
metric. The dashboard aggregates across these authoritative sources without
ever mutating them.
"""

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Income(TimeStampedModel):
    """A single recorded shop income entry."""

    class Category(models.TextChoices):
        ORDER_PAYMENT = "ORDER_PAYMENT", "Order Payment"
        OTHER_INCOME = "OTHER_INCOME", "Other Income"

    category = models.CharField(max_length=20, choices=Category.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    income_date = models.DateField()
    description = models.TextField(blank=True, default="")
    reference = models.CharField(max_length=100, blank=True, default="")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_incomes",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-income_date", "-created_at"]
        verbose_name = "Income"
        verbose_name_plural = "Income Records"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="income_amount_positive",
            )
        ]
        indexes = [
            models.Index(fields=["income_date"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} ({self.income_date})"


class Expense(TimeStampedModel):
    """A single recorded shop expense entry."""

    class Category(models.TextChoices):
        RENT = "RENT", "Rent"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        MATERIAL = "MATERIAL", "Material"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        SHOP_SUPPLIES = "SHOP_SUPPLIES", "Shop Supplies"
        TRANSPORT = "TRANSPORT", "Transport"
        OTHER_EXPENSE = "OTHER_EXPENSE", "Other Expense"

    category = models.CharField(max_length=20, choices=Category.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    description = models.TextField(blank=True, default="")
    reference = models.CharField(max_length=100, blank=True, default="")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_expenses",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-expense_date", "-created_at"]
        verbose_name = "Expense"
        verbose_name_plural = "Expense Records"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="expense_amount_positive",
            )
        ]
        indexes = [
            models.Index(fields=["expense_date"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} ({self.expense_date})"
