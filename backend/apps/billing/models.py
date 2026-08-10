"""Customer billing and invoice models for Saamu Tailors.

Phase 9 introduced the operational billing layer: invoices generated from
existing orders with immutable line-item snapshots, and append-only customer
payments. Phase 11 extends customer payments with explicit payment types
(``ADVANCE`` / ``PARTIAL`` / ``FINAL`` / ``REFUND``) so every transaction is
auditable and refunds are recorded as refunds instead of silently mutating
history. A database-backed ``ShopDetails`` singleton supplies the shop block on
the digital bill.

Billing is deliberately independent of payroll (``apps.payments``) and the
Phase 8 income/expense ledger (``apps.finance``): recording a customer payment
never touches payroll, salary history or the ledger.

``Invoice`` keeps a one-to-one link to an ``Order`` (one invoice per order).
``InvoiceItem`` rows snapshot the order's billing information at invoice time
so later order edits never rewrite historical invoice presentation.
``CustomerPayment`` rows are append-only financial history with no update or
delete path; a REFUND is a normal row whose ``payment_type`` marks it and whose
``refunded_payment`` optionally points back at the transaction it reverses.

Invoice status (UNPAID / PARTIALLY_PAID / PAID) is always DERIVED from the
payment totals at request time; it is never stored, so it cannot go stale.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.customers.models import Customer
from apps.orders.models import Order

MAX_PRICE_DIGITS = 12
MAX_PRICE_DECIMALS = 2


class ShopDetails(TimeStampedModel):
    """Singleton shop profile used on the digital bill.

    The bill must render real database-backed shop information (never mock
    data). This model holds the shop identity established by the project:
    name (Saamu Tailors), the year the family business began (1954), plus
    optional address / phone / tagline editable from the admin. ``shop_details``
    returns the single row, creating it with the established defaults on first
    access.
    """

    name = models.CharField(max_length=100, default="Saamu Tailors")
    tagline = models.CharField(max_length=200, blank=True, default="")
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    established_year = models.PositiveIntegerField(default=1954)
    customer_follow_up_months = models.PositiveSmallIntegerField(
        default=6,
        help_text=(
            "Months of inactivity after which a customer receives a follow-up "
            "reminder. Used by the Reminders V1 customer follow-up rule."
        ),
    )

    class Meta:
        verbose_name = "Shop Details"
        verbose_name_plural = "Shop Details"

    def __str__(self):
        return self.name

    @classmethod
    def shop_details(cls):
        """Return the singleton row, creating it with defaults if missing."""
        instance = cls.objects.first()
        if instance is None:
            instance = cls.objects.create()
        return instance


class Invoice(TimeStampedModel):
    """An invoice generated from an existing order.

    ``invoice_number`` is unique and generated server-side. ``subtotal`` and
    ``total_amount`` are recorded at creation from the line-item snapshots; the
    API re-derives the presentation values (subtotal, total, amount_paid,
    balance_due, status, payment count) from the immutable items and the
    append-only payments.
    """

    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
        PAID = "PAID", "Paid"

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="invoice",
        help_text="The existing order being billed (one invoice per order).",
    )
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Human-friendly unique invoice number, e.g. INV-2026-0001.",
    )
    invoice_date = models.DateField(default=timezone.localdate)
    subtotal = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=MAX_PRICE_DECIMALS,
        default=Decimal("0.00"),
        help_text="Sum of the invoice item line totals at creation time.",
    )
    adjustment_amount = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=MAX_PRICE_DECIMALS,
        default=Decimal("0.00"),
        help_text=(
            "Approved adjustment. Always zero in this phase; no adjustment "
            "rule has been approved."
        ),
    )
    total_amount = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=MAX_PRICE_DECIMALS,
        default=Decimal("0.00"),
        help_text="subtotal + adjustment at creation time.",
    )
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_invoices",
        null=True,
        blank=True,
        help_text="STAFF user who created the invoice (server-side audit).",
    )

    class Meta:
        ordering = ["-invoice_date", "-created_at"]
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        indexes = [
            models.Index(fields=["invoice_date"]),
            models.Index(fields=["order", "invoice_date"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} ({self.order.order_number})"

    def _generate_invoice_number(self):
        """Create the next human-friendly invoice number for the current year.

        Format: ``INV-YYYY-NNNN``, zero-padded so lexicographic ordering matches
        numeric ordering. The database unique constraint on ``invoice_number``
        is the final guard against duplicates.
        """
        year = timezone.localdate().year
        prefix = f"INV-{year}-"
        last = (
            Invoice.objects.filter(invoice_number__startswith=prefix)
            .order_by("-invoice_number")
            .values_list("invoice_number", flat=True)
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
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()
        super().save(*args, **kwargs)


class InvoiceItem(TimeStampedModel):
    """Immutable snapshot of one order line at billing time.

    Values are copied from the order item when the invoice is created. Later
    edits to the order or order item never rewrite historical invoice
    presentation.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    garment_type = models.CharField(
        max_length=20,
        help_text="Snapshot of the garment display label (e.g. 'Shirt').",
    )
    garment_code = models.CharField(
        max_length=10,
        help_text="Snapshot of the garment code (e.g. SHIRT).",
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS, decimal_places=MAX_PRICE_DECIMALS
    )
    line_total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS, decimal_places=MAX_PRICE_DECIMALS
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="invoice_item_quantity_positive",
            )
        ]
        indexes = [
            models.Index(fields=["invoice"]),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.garment_type} on {self.invoice}"


class CustomerPayment(TimeStampedModel):
    """An append-only customer payment against an invoice.

    Payments are financial history: they are never updated or deleted and are
    only ever created through the concurrency-safe service that locks the
    invoice row, so an invoice can never be overpaid.

    ``payment_type`` classifies each transaction: ``ADVANCE`` (a payment made
    toward the order before the balance is cleared), ``PARTIAL`` (pays down but
    does not clear the balance), ``FINAL`` (clears the outstanding balance
    exactly) and ``REFUND`` (money returned to the customer, which reduces the
    total paid). ``refunded_payment`` optionally links a REFUND back to the
    original transaction it reverses, keeping refunds auditable without ever
    altering the original row.
    """

    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        UPI = "UPI", "UPI"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
        OTHER = "OTHER", "Other"

    class PaymentType(models.TextChoices):
        ADVANCE = "ADVANCE", "Advance"
        PARTIAL = "PARTIAL", "Partial"
        FINAL = "FINAL", "Final"
        REFUND = "REFUND", "Refund"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="payments"
    )
    payment_type = models.CharField(
        max_length=12,
        choices=PaymentType.choices,
        default=PaymentType.PARTIAL,
        help_text="ADVANCE / PARTIAL / FINAL payment or a REFUND to the customer.",
    )
    refunded_payment = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunds",
        help_text=(
            "For REFUND transactions, the original payment being reversed "
            "(audit trail). The original row is never modified."
        ),
    )
    amount = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS, decimal_places=MAX_PRICE_DECIMALS
    )
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_customer_payments",
        null=True,
        blank=True,
        help_text="STAFF user who recorded the payment (server-side audit).",
    )

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        verbose_name = "Customer Payment"
        verbose_name_plural = "Customer Payments"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="customer_payment_amount_positive",
            )
        ]
        indexes = [
            models.Index(fields=["invoice", "payment_date"]),
            models.Index(fields=["payment_method"]),
            models.Index(fields=["payment_type"]),
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.amount} ({self.get_payment_type_display()})"


class ManualReminder(TimeStampedModel):
    """A manually-created reminder, the only persisted reminder in Reminders V1.

    Every automatic reminder (overdue orders, due dates, ready-for-pickup,
    outstanding payments, tailor workload, missing measurements, customer
    follow-up) is derived on demand and never stored. This model exists so
    staff can capture follow-ups that the automatic rules cannot express, and
    to track them to completion (PENDING -> COMPLETED / CANCELLED). Rows are
    never physically deleted: cancelled reminders remain as an audit trail.
    """

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    title = models.CharField(
        max_length=200, help_text="Short headline for the reminder."
    )
    description = models.TextField(blank=True, max_length=4000)
    reminder_date = models.DateField(
        help_text="Date this reminder is due / should be actioned."
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manual_reminders",
        help_text="Optional related customer for context.",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manual_reminders",
        help_text="Optional related order for context.",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_manual_reminders",
        null=True,
        blank=True,
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="completed_manual_reminders",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-reminder_date", "-id"]
        verbose_name = "Manual Reminder"
        verbose_name_plural = "Manual Reminders"
        indexes = [
            models.Index(fields=["status", "reminder_date"]),
            models.Index(fields=["priority"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
