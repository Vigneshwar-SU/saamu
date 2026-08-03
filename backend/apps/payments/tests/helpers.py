"""Shared helpers for payments and settlement tests."""

from datetime import date, timedelta

from django.utils import timezone

from apps.payments.models import PayrollPayment, SalaryAdvance
from apps.payroll.models import PayrollPeriod
from apps.payroll.tests.helpers import (  # noqa: F401
    create_completed_assignment,
    create_payroll_period,
    make_owner,
    make_staff,
)
from apps.tailors.tests.helpers import (
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
)


def advances_url():
    return "/api/v1/advances/"


def advance_url(advance_id):
    return f"/api/v1/advances/{advance_id}/"


def entry_settlement_url(entry_id):
    return f"/api/v1/payroll/entries/{entry_id}/settlement/"


def entry_payments_url(entry_id):
    return f"/api/v1/payroll/entries/{entry_id}/payments/"


def entry_settle_url(entry_id):
    return f"/api/v1/payroll/entries/{entry_id}/settle/"


def entry_apply_advance_url(entry_id):
    return f"/api/v1/payroll/entries/{entry_id}/apply-advance/"


def create_advance(tailor, amount="500.00", advance_date=None, **kwargs):
    defaults = {
        "tailor": tailor,
        "amount": amount,
        "advance_date": advance_date or date.today(),
    }
    defaults.update(kwargs)
    return SalaryAdvance.objects.create(**defaults)


def create_payment(entry, amount="300.00", payment_date=None, **kwargs):
    defaults = {
        "payroll_entry": entry,
        "tailor": entry.tailor,
        "amount": amount,
        "payment_date": payment_date or date.today(),
        "payment_method": PayrollPayment.Method.CASH,
    }
    defaults.update(kwargs)
    return PayrollPayment.objects.create(**defaults)


def create_finalized_entry(**tailor_kwargs):
    """Build a FINALIZED payroll period with a single piece-rate entry.

    The default setup yields one entry with 5 completed SHIRT pieces at
    ``150.00`` each, i.e. ``total_payable == 750.00``.
    """
    customer = create_customer()
    tailor = create_tailor(**tailor_kwargs)
    order = create_order_with_items(customer, {"SHIRT": 10})
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=date.today() - timedelta(days=7), period_end=date.today()
    )
    create_completed_assignment(tailor, item, 5, 5, "150.00", timezone.now())
    period.calculate()
    period.status = PayrollPeriod.Status.FINALIZED
    period.save(update_fields=["status", "updated_at"])
    return period.entries.get(tailor=tailor)
