"""Invoice and customer payment services for Phase 9.

All financially sensitive mutations live here:

- ``create_invoice_for_order`` creates an invoice plus immutable item snapshots
  atomically, guarding the one-invoice-per-order rule and the unique
  server-generated invoice number.
- ``record_customer_payment`` records an append-only payment inside
  ``transaction.atomic()`` after locking the invoice row with
  ``select_for_update()``, so concurrent requests can never overpay an invoice
  or drive the balance negative.

Derived invoice presentation (subtotal, total, amount_paid, balance_due,
status, payment count) is computed on the fly from the immutable line items and
the append-only payments; a mutable status is never stored, so it cannot go
stale. All money arithmetic uses Decimal.
"""

from datetime import date as _date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import CustomerPayment, Invoice, InvoiceItem

ZERO = Decimal("0.00")


def invoice_summary(invoice):
    """Derive the presentation values for an invoice.

    ``subtotal`` = sum of the immutable line-item totals, ``total`` = subtotal +
    adjustment, ``amount_paid`` = sum of the append-only payments,
    ``balance_due`` = total - amount_paid and the status is derived from those
    two values (UNPAID when nothing is paid, PAID when the balance is zero,
    otherwise PARTIALLY_PAID).
    """
    subtotal = sum((item.line_total for item in invoice.items.all()), ZERO)
    adjustment = invoice.adjustment_amount
    total = subtotal + adjustment
    paid = sum((payment.amount for payment in invoice.payments.all()), ZERO)
    balance = total - paid

    if paid == 0:
        status = Invoice.Status.UNPAID
    elif balance == 0:
        status = Invoice.Status.PAID
    else:
        status = Invoice.Status.PARTIALLY_PAID

    return {
        "subtotal": subtotal,
        "adjustment_amount": adjustment,
        "total_amount": total,
        "amount_paid": paid,
        "balance_due": balance,
        "status": status,
        "payment_count": invoice.payments.count(),
    }


def create_invoice_for_order(*, order, invoice_date=None, notes="", created_by=None):
    """Create an invoice from an existing order with immutable item snapshots.

    The order must exist and must not already have an invoice (enforced by the
    OneToOne field plus a friendly validation error). The invoice number is
    generated server-side; the database unique constraint is the final guard,
    and a concurrent number collision retries with a fresh number.
    """
    if invoice_date is None:
        invoice_date = timezone.localdate()
    elif isinstance(invoice_date, str):
        try:
            invoice_date = _date.fromisoformat(invoice_date.strip())
        except ValueError:
            raise ValidationError({"invoice_date": "Enter a valid date (YYYY-MM-DD)."})

    if Invoice.objects.filter(order_id=order.id).exists():
        raise ValidationError({"order": "An invoice already exists for this order."})

    item_snapshots = []
    subtotal = ZERO
    for item in order.items.all():
        line_total = item.unit_price * item.quantity
        subtotal += line_total
        item_snapshots.append(
            InvoiceItem(
                garment_type=item.get_garment_type_display(),
                garment_code=item.garment_type,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=line_total,
            )
        )

    for attempt in range(3):
        try:
            with transaction.atomic():
                invoice = Invoice.objects.create(
                    order=order,
                    invoice_date=invoice_date,
                    subtotal=subtotal,
                    adjustment_amount=ZERO,
                    total_amount=subtotal,
                    notes=notes or "",
                    created_by=created_by,
                )
                for snapshot in item_snapshots:
                    snapshot.invoice = invoice
                InvoiceItem.objects.bulk_create(item_snapshots)
            return invoice
        except IntegrityError:
            # Either a duplicate invoice for this order (raced) or an invoice
            # number collision. The friendly order check takes precedence.
            if Invoice.objects.filter(order_id=order.id).exists():
                raise ValidationError(
                    {"order": "An invoice already exists for this order."}
                )
            if attempt >= 2:
                raise


def record_customer_payment(
    *,
    invoice,
    amount,
    payment_date=None,
    payment_method,
    reference="",
    notes="",
    recorded_by=None,
):
    """Record an append-only customer payment, refusing overpayment.

    The invoice row is locked with ``select_for_update()`` inside the atomic
    block and the current balance is recomputed from the append-only payments,
    so two concurrent requests cannot both pass the balance check and drive the
    balance negative.
    """
    amount = Decimal(str(amount))
    if amount <= ZERO:
        raise ValidationError({"amount": "Payment amount must be greater than zero."})
    if payment_method not in CustomerPayment.Method.values:
        raise ValidationError({"payment_method": "Invalid payment method."})
    if payment_date is None:
        payment_date = timezone.localdate()

    with transaction.atomic():
        locked = Invoice.objects.select_for_update().get(pk=invoice.id)
        balance = invoice_summary(locked)["balance_due"]
        if amount > balance:
            raise ValidationError(
                {
                    "amount": (
                        "Payment cannot exceed the outstanding balance of "
                        f"{balance}."
                    )
                }
            )
        payment = CustomerPayment.objects.create(
            invoice=locked,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference=reference or "",
            notes=notes or "",
            recorded_by=recorded_by,
        )
    return payment
