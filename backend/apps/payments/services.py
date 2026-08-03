"""Settlement computation and concurrency-safe settlement mutations.

All settlement values are derived, never stored: ``gross_payable`` comes from
the immutable Phase 6 ``PayrollEntry.total_payable``; ``advance_deductions``
and ``payments_recorded`` are aggregated from linked rows;
``outstanding_payable`` and ``settlement_status`` follow from those values.
The status values are UNPAID / PARTIALLY_PAID / SETTLED.

Every mutation that changes outstanding (record a payment, apply an advance,
settle an entry) runs inside ``transaction.atomic()`` and locks the payroll
entry row with ``select_for_update()``, so concurrent operations can never
overpay a single entry. Applying an advance additionally locks the advance row
so it cannot be deducted twice.
"""

from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.payroll.models import PayrollEntry, PayrollPeriod

from .models import PayrollPayment, SalaryAdvance

ZERO = Decimal("0.00")


def _advance_deductions(entry):
    return (
        SalaryAdvance.objects.filter(
            payroll_entry=entry, status=SalaryAdvance.Status.DEDUCTED
        ).aggregate(total=models.Sum("amount"))["total"]
        or ZERO
    )


def _payments_total(entry):
    return (
        PayrollPayment.objects.filter(payroll_entry=entry).aggregate(
            total=models.Sum("amount")
        )["total"]
        or ZERO
    )


def outstanding_payable(entry):
    """Server-derived outstanding amount for one payroll entry."""
    return entry.total_payable - _advance_deductions(entry) - _payments_total(entry)


def settlement_summary(entry):
    """Derive the settlement values for one payroll entry.

    Returns gross_payable, advance_deductions, payments_recorded,
    outstanding_payable, settlement_status and payment_count. The summary is
    purely derived and works for any payroll period state; mutations are only
    permitted on FINALIZED periods.
    """
    gross = entry.total_payable
    deductions = _advance_deductions(entry)
    paid = _payments_total(entry)
    payment_count = PayrollPayment.objects.filter(payroll_entry=entry).count()
    outstanding = gross - deductions - paid

    if outstanding <= ZERO:
        status = "SETTLED"
    elif paid > ZERO or deductions > ZERO:
        status = "PARTIALLY_PAID"
    else:
        status = "UNPAID"

    return {
        "gross_payable": gross,
        "advance_deductions": deductions,
        "payments_recorded": paid,
        "outstanding_payable": outstanding,
        "settlement_status": status,
        "payment_count": payment_count,
    }


def period_settlement_summary(period):
    """Aggregate settlement values across every entry of a payroll period.

    Mirrors the shape of :func:`settlement_summary` so the frontend can reuse
    one type for both entry-level and period-level summaries.
    """
    gross = period.entries.aggregate(total=models.Sum("total_payable"))["total"] or ZERO
    deductions = (
        SalaryAdvance.objects.filter(
            payroll_entry__payroll_period=period,
            status=SalaryAdvance.Status.DEDUCTED,
        ).aggregate(total=models.Sum("amount"))["total"]
        or ZERO
    )
    paid = (
        PayrollPayment.objects.filter(payroll_entry__payroll_period=period).aggregate(
            total=models.Sum("amount")
        )["total"]
        or ZERO
    )
    payment_count = PayrollPayment.objects.filter(
        payroll_entry__payroll_period=period
    ).count()
    outstanding = gross - deductions - paid

    if gross <= ZERO:
        status = "UNPAID"
    elif outstanding <= ZERO:
        status = "SETTLED"
    elif paid > ZERO or deductions > ZERO:
        status = "PARTIALLY_PAID"
    else:
        status = "UNPAID"

    return {
        "gross_payable": gross,
        "advance_deductions": deductions,
        "payments_recorded": paid,
        "outstanding_payable": outstanding,
        "settlement_status": status,
        "payment_count": payment_count,
    }


def _get_locked_entry(entry_id):
    """Fetch and lock a payroll entry, refusing non-finalized periods."""
    entry = PayrollEntry.objects.select_for_update().get(pk=entry_id)
    if entry.payroll_period.status != PayrollPeriod.Status.FINALIZED:
        raise ValidationError(
            {"detail": "Only finalized payroll periods can be settled."}
        )
    return entry


def record_payment(
    *, entry, amount, payment_date, payment_method, reference="", notes="", recorded_by
):
    """Record a payroll payment, refusing overpayment.

    The payment amount must be positive and must not exceed the server-derived
    outstanding payable. The entry row is locked for the duration so concurrent
    payments cannot overshoot.
    """
    amount = Decimal(str(amount))
    if amount <= ZERO:
        raise ValidationError({"amount": "Payment amount must be greater than zero."})
    if payment_method not in PayrollPayment.Method.values:
        raise ValidationError({"payment_method": "Invalid payment method."})

    with transaction.atomic():
        locked = _get_locked_entry(entry.id)
        outstanding = outstanding_payable(locked)
        if amount > outstanding:
            raise ValidationError(
                {
                    "amount": (
                        "Payment cannot exceed the outstanding payable of "
                        f"{outstanding}."
                    )
                }
            )
        payment = PayrollPayment.objects.create(
            payroll_entry=locked,
            tailor=locked.tailor,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference=reference or "",
            notes=notes or "",
            recorded_by=recorded_by,
        )
    return payment, settlement_summary(entry)


def apply_advance(*, entry, advance, recorded_by):
    """Deduct an OUTSTANDING advance against a finalized payroll entry.

    The advance and the entry are both locked. The advance must belong to the
    entry's tailor, must still be OUTSTANDING, and must not exceed the
    outstanding payable (a deduction can never make payable negative).
    """
    with transaction.atomic():
        locked_entry = _get_locked_entry(entry.id)
        locked_advance = SalaryAdvance.objects.select_for_update().get(pk=advance.id)

        if locked_advance.tailor_id != locked_entry.tailor_id:
            raise ValidationError(
                {"advance": "The advance belongs to a different tailor."}
            )
        if locked_advance.status != SalaryAdvance.Status.OUTSTANDING:
            raise ValidationError(
                {"advance": "This advance has already been deducted."}
            )
        if locked_advance.amount > outstanding_payable(locked_entry):
            raise ValidationError(
                {
                    "advance": (
                        "This advance exceeds the outstanding payable for the "
                        "payroll entry."
                    )
                }
            )

        locked_advance.status = SalaryAdvance.Status.DEDUCTED
        locked_advance.payroll_entry = locked_entry
        locked_advance.deducted_at = timezone.now()
        locked_advance.save(
            update_fields=["status", "payroll_entry", "deducted_at", "updated_at"]
        )
    return locked_advance, settlement_summary(entry)


def settle_entry(
    *, entry, payment_date, payment_method, reference="", notes="", recorded_by
):
    """Settle a payroll entry fully by recording one final payment.

    The payment covers the entire server-derived outstanding payable. This is
    an optional explicit full-settlement action; a partial payment of the full
    outstanding amount is equivalent.
    """
    if payment_method not in PayrollPayment.Method.values:
        raise ValidationError({"payment_method": "Invalid payment method."})

    with transaction.atomic():
        locked = _get_locked_entry(entry.id)
        outstanding = outstanding_payable(locked)
        if outstanding <= ZERO:
            raise ValidationError(
                {"detail": "This payroll entry is already fully settled."}
            )
        payment = PayrollPayment.objects.create(
            payroll_entry=locked,
            tailor=locked.tailor,
            amount=outstanding,
            payment_date=payment_date,
            payment_method=payment_method,
            reference=reference or "",
            notes=notes or "",
            recorded_by=recorded_by,
        )
    return payment, settlement_summary(entry)
