"""Shared helpers for payroll tests."""

from datetime import date

from apps.customers.tests.helpers import make_owner, make_staff  # noqa: F401
from apps.payroll.models import PayrollPeriod
from apps.tailors.models import WorkAssignment
from apps.tailors.tests.helpers import create_assignment


def payroll_periods_url():
    return "/api/v1/payroll/periods/"


def payroll_period_url(period_id):
    return f"/api/v1/payroll/periods/{period_id}/"


def payroll_calculate_url(period_id):
    return f"/api/v1/payroll/periods/{period_id}/calculate/"


def payroll_finalize_url(period_id):
    return f"/api/v1/payroll/periods/{period_id}/finalize/"


def payroll_entries_url():
    return "/api/v1/payroll/entries/"


def payroll_tailor_detail_url(period_id, tailor_id):
    return f"/api/v1/payroll/periods/{period_id}/tailors/{tailor_id}/"


def create_payroll_period(
    period_start=None, period_end=None, status=PayrollPeriod.Status.DRAFT, **kwargs
):
    today = date.today()
    defaults = {
        "period_start": period_start or today,
        "period_end": period_end or today,
        "status": status,
    }
    defaults.update(kwargs)
    return PayrollPeriod.objects.create(**defaults)


def create_completed_assignment(
    tailor,
    order_item,
    assigned_quantity,
    completed_quantity,
    rate_per_piece_snapshot,
    completed_at,
):
    assignment = create_assignment(
        tailor,
        order_item,
        assigned_quantity=assigned_quantity,
        completed_quantity=completed_quantity,
        status=WorkAssignment.Status.COMPLETED,
        rate_per_piece_snapshot=rate_per_piece_snapshot,
    )
    assignment.completed_at = completed_at
    assignment.save(update_fields=["completed_at"])
    return assignment
