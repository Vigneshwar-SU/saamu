"""Dashboard summary aggregation for Phase 8.

The dashboard is read-only: every figure is derived on the fly from
authoritative source records and never mutates them. Financial metrics come
from four independent sources so nothing is silently reclassified:

- ``Income`` / ``Expense``  -> recorded ledger totals and net balance
- ``PayrollPayment``       -> payroll actually paid out
- ``SalaryAdvance``        -> a separate advance metric, never treated as expense
- ``Order.total_amount``   -> order revenue, clearly distinct from recorded cash

Operational metrics (orders, garments, workload, active counts) come from
``apps.orders`` / ``apps.tailors`` / ``apps.customers``. All monetary
arithmetic uses ``Decimal`` and is rounded to two places for the API.
"""

from decimal import Decimal

from django.db.models import Count, Sum

from apps.customers.models import Customer, GarmentType
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.payments.models import PayrollPayment, SalaryAdvance
from apps.tailors.models import Tailor, WorkAssignment

from .models import Expense, Income
from .serializers import ExpenseSerializer, IncomeSerializer

RECENT_LIMIT = 5


def _range_kwargs(date_from, date_to, date_field):
    """Build inclusive ``__gte``/``__lte`` filter kwargs for a date field."""
    filters = {}
    if date_from is not None:
        filters[f"{date_field}__gte"] = date_from
    if date_to is not None:
        filters[f"{date_field}__lte"] = date_to
    return filters


def _decimal_sum(queryset, field):
    total = queryset.aggregate(total=Sum(field))["total"]
    return total if total is not None else Decimal("0.00")


def _workload_totals():
    """Aggregate assigned/completed/outstanding pieces and piece-rate earnings
    across all work assignments (current shop workload)."""
    totals = {
        "assigned_quantity": 0,
        "completed_quantity": 0,
        "outstanding_quantity": 0,
        "earned_amount": Decimal("0.00"),
    }
    for assignment in WorkAssignment.objects.all().select_related("order_item"):
        outstanding = max(
            assignment.assigned_quantity - assignment.completed_quantity, 0
        )
        earned = assignment.completed_quantity * assignment.rate_per_piece_snapshot
        totals["assigned_quantity"] += assignment.assigned_quantity
        totals["completed_quantity"] += assignment.completed_quantity
        totals["outstanding_quantity"] += outstanding
        totals["earned_amount"] += earned
    totals["earned_amount"] = round(totals["earned_amount"], 2)
    return totals


def build_dashboard_summary(date_from=None, date_to=None, request=None):
    """Build the full dashboard summary for an inclusive date range.

    ``request`` is optional and only used to serialize the recent records with
    the correct serializer context.
    """
    income_filters = _range_kwargs(date_from, date_to, "income_date")
    expense_filters = _range_kwargs(date_from, date_to, "expense_date")
    payment_filters = _range_kwargs(date_from, date_to, "payment_date")
    advance_filters = _range_kwargs(date_from, date_to, "advance_date")
    order_filters = _range_kwargs(date_from, date_to, "order_date")

    recorded_income = _decimal_sum(Income.objects.filter(**income_filters), "amount")
    recorded_expenses = _decimal_sum(
        Expense.objects.filter(**expense_filters), "amount"
    )
    payroll_paid = _decimal_sum(
        PayrollPayment.objects.filter(**payment_filters), "amount"
    )
    salary_advances = _decimal_sum(
        SalaryAdvance.objects.filter(**advance_filters), "amount"
    )
    order_revenue = _decimal_sum(Order.objects.filter(**order_filters), "total_amount")

    orders = Order.objects.filter(**order_filters)
    order_counts = {status: 0 for status in OrderStatus.values}
    order_counts["total"] = orders.count()
    for row in orders.values("status").annotate(count=Count("id")):
        order_counts[row["status"]] = row["count"]

    garment_quantities = {code: 0 for code in GarmentType.values}
    item_rows = (
        OrderItem.objects.filter(order__in=orders.values("id"))
        .values("garment_type")
        .annotate(total=Sum("quantity"))
    )
    for row in item_rows:
        garment_quantities[row["garment_type"]] = int(row["total"] or 0)

    recent_income_qs = (
        Income.objects.select_related("recorded_by")
        .all()
        .order_by("-income_date", "-created_at")[:RECENT_LIMIT]
    )
    recent_expenses_qs = (
        Expense.objects.select_related("recorded_by")
        .all()
        .order_by("-expense_date", "-created_at")[:RECENT_LIMIT]
    )

    return {
        "success": True,
        "financial": {
            "recorded_income": round(recorded_income, 2),
            "recorded_expenses": round(recorded_expenses, 2),
            "net_recorded_balance": round(recorded_income - recorded_expenses, 2),
            "payroll_paid": round(payroll_paid, 2),
            "salary_advances": round(salary_advances, 2),
            "order_revenue": round(order_revenue, 2),
        },
        "operational": {
            "order_counts": order_counts,
            "garment_quantities": garment_quantities,
            "workload": _workload_totals(),
            "active_customers": Customer.objects.filter(is_active=True).count(),
            "active_tailors": Tailor.objects.filter(is_active=True).count(),
        },
        "recent_income": IncomeSerializer(
            recent_income_qs, many=True, context={"request": request}
        ).data,
        "recent_expenses": ExpenseSerializer(
            recent_expenses_qs, many=True, context={"request": request}
        ).data,
    }
