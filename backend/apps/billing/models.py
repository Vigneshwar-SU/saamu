"""Customer billing and invoice models for Saamu Tailors.

Phase 9 introduces a separate operational billing layer: invoices generated
from existing orders with immutable line-item snapshots, and append-only
customer payments. Billing is deliberately independent of payroll
(``apps.payments``) and the Phase 8 income/expense ledger (``apps.finance``):
recording a customer payment never touches payroll, salary history or the
ledger.

``Invoice`` keeps a one-to-one link to an ``Order`` (one invoice per order).
``InvoiceItem`` rows snapshot the order's billing information at invoice time
so later order edits never rewrite historical invoice presentation.
``CustomerPayment`` rows are append-only financial history with no update or
delete path.

Invoice status (UNPAID / PARTIALLY_PAID / PAID) is always DERIVED from the
payment totals at request time; it is never stored, so it cannot go stale.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.orders.models import Order

MAX_PRICE_DIGITS = 12
MAX_PRICE_DECIMALS = 2


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
    """

    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        UPI = "UPI", "UPI"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
        OTHER = "OTHER", "Other"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="payments"
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
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.amount} ({self.get_payment_method_display()})"
