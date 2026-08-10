"""Invoice and customer payment services for Phase 9 + Phase 11.

All financially sensitive mutations live here:

- ``create_invoice_for_order`` creates an invoice plus immutable item snapshots
  atomically, guarding the one-invoice-per-order rule and the unique
  server-generated invoice number.
- ``record_customer_payment`` records an append-only payment (typed
  ``ADVANCE`` / ``PARTIAL`` / ``FINAL`` / ``REFUND``) inside
  ``transaction.atomic()`` after locking the invoice row with
  ``select_for_update()``, so concurrent requests can never overpay an invoice,
  clear it with an invalid FINAL, or refund more than the customer has paid.

Derived invoice presentation (subtotal, total, gross/refunded/net paid,
balance, status, payment count) is computed on the fly from the immutable line
items and the append-only payments; a mutable status is never stored, so it
cannot go stale. All money arithmetic uses Decimal.
"""

from datetime import date as _date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import CustomerPayment, Invoice, InvoiceItem, ShopDetails

ZERO = Decimal("0.00")


def invoice_summary(invoice):
    """Derive the presentation values for an invoice.

    ``subtotal`` = sum of the immutable line-item totals, ``total`` = subtotal +
    adjustment, ``gross_paid`` = sum of non-REFUND payments, ``refunded_amount``
    = sum of REFUND payments, ``amount_paid`` (net) = gross_paid - refunded and
    ``balance_due`` = total - net paid. The status is derived from those two
    values: UNPAID when nothing is net-paid, PAID when the balance is zero,
    otherwise PARTIALLY_PAID.
    """
    subtotal = sum((item.line_total for item in invoice.items.all()), ZERO)
    adjustment = invoice.adjustment_amount
    total = subtotal + adjustment
    payments = list(invoice.payments.all())
    gross_paid = sum(
        (
            payment.amount
            for payment in payments
            if payment.payment_type != CustomerPayment.PaymentType.REFUND
        ),
        ZERO,
    )
    refunded = sum(
        (
            payment.amount
            for payment in payments
            if payment.payment_type == CustomerPayment.PaymentType.REFUND
        ),
        ZERO,
    )
    net_paid = gross_paid - refunded
    balance = total - net_paid

    if net_paid == 0:
        status = Invoice.Status.UNPAID
    elif balance == 0:
        status = Invoice.Status.PAID
    else:
        status = Invoice.Status.PARTIALLY_PAID

    return {
        "subtotal": subtotal,
        "adjustment_amount": adjustment,
        "total_amount": total,
        "gross_paid": gross_paid,
        "refunded_amount": refunded,
        "amount_paid": net_paid,
        "balance_due": balance,
        "status": status,
        "payment_count": len(payments),
    }


def order_payment_summary(order):
    """Authoritative payment summary for an order.

    ``order_total`` is the order's stored total; ``total_paid``,
    ``outstanding_balance`` and ``payment_status`` are derived from the order's
    invoice payment history (zeroed when no invoice has been raised). The
    backend remains authoritative for every financial value - the frontend only
    ever displays these figures.
    """
    invoice = Invoice.objects.filter(order=order).first()
    order_total = order.total_amount
    if invoice is None:
        return {
            "order_total": order_total,
            "total_paid": ZERO,
            "outstanding_balance": order_total,
            "payment_status": Invoice.Status.UNPAID,
            "payment_count": 0,
            "refunded_amount": ZERO,
            "has_invoice": False,
        }
    summary = invoice_summary(invoice)
    return {
        "order_total": order_total,
        "total_paid": summary["amount_paid"],
        "outstanding_balance": summary["balance_due"],
        "payment_status": summary["status"],
        "payment_count": summary["payment_count"],
        "refunded_amount": summary["refunded_amount"],
        "has_invoice": True,
    }


def shop_details_data():
    """Return the database-backed shop profile as plain data for the bill."""
    details = ShopDetails.shop_details()
    return {
        "name": details.name,
        "tagline": details.tagline,
        "address": details.address,
        "phone": details.phone,
        "established_year": details.established_year,
    }


def build_bill_data(invoice):
    """Assemble every value the digital bill renders, all from the database.

    The bill is a read-only presentation of real data: the shop block comes
    from the ``ShopDetails`` singleton, the customer from the order, the
    garments from the immutable invoice item snapshots, the payment history and
    running totals from the append-only payments, and the dates from the order
    and invoice. No mock or client-supplied data ever reaches the bill.
    """
    order = invoice.order
    customer = order.customer
    payments = list(invoice.payments.select_related("recorded_by").all())
    items = list(invoice.items.all())
    summary = invoice_summary(invoice)

    return {
        "shop": shop_details_data(),
        "bill_metadata": {
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "generated_at": timezone.localtime(timezone.now()).isoformat(),
        },
        "customer": {
            "full_name": customer.full_name,
            "mobile_number": customer.mobile_number,
        },
        "order": {
            "order_number": order.order_number,
            "order_date": order.order_date,
            "expected_delivery_date": order.expected_delivery_date,
            "status": order.status,
        },
        "garments": [
            {
                "garment_type": item.garment_type,
                "garment_code": item.garment_code,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "line_total": item.line_total,
            }
            for item in items
        ],
        "payment_history": [
            {
                "id": payment.id,
                "payment_type": payment.payment_type,
                "payment_type_display": payment.get_payment_type_display(),
                "amount": payment.amount,
                "payment_date": payment.payment_date,
                "payment_method": payment.payment_method,
                "payment_method_display": payment.get_payment_method_display(),
                "reference": payment.reference,
                "notes": payment.notes,
                "recorded_by": (
                    payment.recorded_by.username if payment.recorded_by else None
                ),
            }
            for payment in payments
        ],
        "totals": {
            "subtotal": summary["subtotal"],
            "adjustment_amount": summary["adjustment_amount"],
            "total_amount": summary["total_amount"],
            "gross_paid": summary["gross_paid"],
            "refunded_amount": summary["refunded_amount"],
            "amount_paid": summary["amount_paid"],
            "balance_due": summary["balance_due"],
            "status": summary["status"],
        },
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
        raise ValidationError({"order": "This order already has an invoice."})

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
                raise ValidationError({"order": "This order already has an invoice."})
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
    payment_type=None,
    refunded_payment=None,
):
    """Record an append-only customer payment, refusing invalid financial states.

    The invoice row is locked with ``select_for_update()`` inside the atomic
    block and the current balance / net paid are recomputed from the
    append-only payments, so two concurrent requests cannot both pass the
    balance check and drive the balance negative.

    ``payment_type`` is validated against the server-derived values:

    - ``ADVANCE``: amount must not exceed the outstanding balance.
    - ``PARTIAL``: amount must be strictly less than the outstanding balance
      (a payment that clears the balance is a FINAL).
    - ``FINAL``: amount must equal the outstanding balance exactly.
    - ``REFUND``: amount must not exceed the total paid (net of earlier
      refunds), so total paid never goes negative. ``refunded_payment`` may
      link the refund back to the original transaction for auditability.

    When ``payment_type`` is omitted it is derived from the amount: FINAL when
    the amount clears the balance, otherwise PARTIAL (Phase 9 behaviour).
    """
    amount = Decimal(str(amount))
    if amount <= ZERO:
        raise ValidationError({"amount": "Payment amount must be greater than zero."})
    if payment_method not in CustomerPayment.Method.values:
        raise ValidationError({"payment_method": "Invalid payment method."})
    if (
        payment_type is not None
        and payment_type not in CustomerPayment.PaymentType.values
    ):
        raise ValidationError({"payment_type": "Invalid payment type."})
    if payment_date is None:
        payment_date = timezone.localdate()

    with transaction.atomic():
        locked = Invoice.objects.select_for_update().get(pk=invoice.id)
        summary = invoice_summary(locked)
        balance = summary["balance_due"]
        net_paid = summary["amount_paid"]

        resolved_type = payment_type
        if resolved_type is None:
            resolved_type = (
                CustomerPayment.PaymentType.FINAL
                if amount == balance
                else CustomerPayment.PaymentType.PARTIAL
            )

        linked_refund = None
        if resolved_type == CustomerPayment.PaymentType.REFUND:
            if amount > net_paid:
                raise ValidationError(
                    {
                        "amount": (
                            "A refund cannot exceed the total paid of " f"{net_paid}."
                        )
                    }
                )
            if refunded_payment is not None:
                refund_pk = getattr(refunded_payment, "pk", refunded_payment)
                linked_refund = CustomerPayment.objects.filter(pk=refund_pk).first()
                if linked_refund is None or linked_refund.invoice_id != locked.id:
                    raise ValidationError(
                        {
                            "refunded_payment": (
                                "The refunded payment does not exist or does not "
                                "belong to this invoice."
                            )
                        }
                    )
                if linked_refund.payment_type == CustomerPayment.PaymentType.REFUND:
                    raise ValidationError(
                        {
                            "refunded_payment": (
                                "A refund cannot reference another refund."
                            )
                        }
                    )
        else:
            if amount > balance:
                raise ValidationError(
                    {
                        "amount": (
                            "Payment cannot exceed the outstanding balance of "
                            f"{balance}."
                        )
                    }
                )
            if (
                resolved_type == CustomerPayment.PaymentType.PARTIAL
                and amount == balance
            ):
                raise ValidationError(
                    {
                        "amount": (
                            "A PARTIAL payment must be less than the outstanding "
                            "balance. Use FINAL to settle the balance."
                        )
                    }
                )
            if resolved_type == CustomerPayment.PaymentType.FINAL and amount != balance:
                raise ValidationError(
                    {
                        "amount": (
                            "A FINAL payment must equal the outstanding balance "
                            f"of {balance}."
                        )
                    }
                )

        payment = CustomerPayment.objects.create(
            invoice=locked,
            payment_type=resolved_type,
            refunded_payment=linked_refund,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference=reference or "",
            notes=notes or "",
            recorded_by=recorded_by,
        )
    return payment
