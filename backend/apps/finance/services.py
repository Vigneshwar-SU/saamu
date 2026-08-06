"""Dashboard, income summary, expense summary and reports aggregation.

The dashboard and reports layer are read-only: every figure is derived on the
fly from authoritative source records and never mutates them. Financial
metrics come from independent sources so nothing is silently reclassified:

- ``CustomerPayment``     -> customer-derived net income (payments - refunds)
- ``Expense``             -> recorded expense ledger totals
- ``PayrollPayment``      -> payroll actually paid out
- ``SalaryAdvance``       -> a separate advance metric, never treated as expense
- ``Order.total_amount``  -> order revenue, clearly distinct from recorded cash

Income (Phase 13) is never maintained manually: it is always derived from the
append-only customer payments, where each non-REFUND payment contributes to
income exactly once and every REFUND reduces net income. ``build_income_summary``
is the single authoritative aggregation used by the income API, the dashboard
and the reports API, so they can never disagree.

Operational metrics (orders, garments, workload, active counts) come from
``apps.orders`` / ``apps.tailors`` / ``apps.customers``. All monetary
arithmetic uses ``Decimal`` and is rounded to two places for the API.

Reports (Phase 14) is a thin read-only layer over the same authoritative
sources: ``build_reports_summary`` reuses ``build_income_summary`` and
``build_expense_summary`` verbatim (so report income always agrees with the
Phase 13 income summary and report expenses always agree with the Phase 12
expense summary) and derives the net position server-side without storing a
new financial record.
"""

from decimal import Decimal

from django.db.models import Case, Count, DecimalField, F, Q, Sum, When

from apps.billing.models import CustomerPayment
from apps.customers.models import Customer, GarmentType
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.payments.models import PayrollPayment, SalaryAdvance
from apps.tailors.models import Tailor, WorkAssignment

from .models import Expense
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
    expense_filters = _range_kwargs(date_from, date_to, "expense_date")
    payment_filters = _range_kwargs(date_from, date_to, "payment_date")
    advance_filters = _range_kwargs(date_from, date_to, "advance_date")
    order_filters = _range_kwargs(date_from, date_to, "order_date")

    recorded_income = build_income_summary(date_from, date_to)["total_income"]
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

    recent_payments_qs = (
        CustomerPayment.objects.select_related(
            "invoice__order__customer", "recorded_by"
        )
        .all()
        .order_by("-payment_date", "-created_at")[:RECENT_LIMIT]
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
        "recent_payments": IncomeSerializer(
            recent_payments_qs, many=True, context={"request": request}
        ).data,
        "recent_expenses": ExpenseSerializer(
            recent_expenses_qs, many=True, context={"request": request}
        ).data,
    }


def _income_filters(date_from, date_to, payment_method=None, payment_type=None):
    """Build the inclusive filter kwargs shared by income list and summary."""
    filters = _range_kwargs(date_from, date_to, "payment_date")
    if payment_method:
        filters["payment_method"] = payment_method
    if payment_type:
        filters["payment_type"] = payment_type
    return filters


def build_income_summary(
    date_from=None, date_to=None, payment_method=None, payment_type=None
):
    """Customer-derived income summary over an inclusive date range.

    Income is derived from append-only customer payments: every non-REFUND
    payment (ADVANCE / PARTIAL / FINAL) contributes to income exactly once and
    every REFUND reduces net income, matching the invoice-level refund logic in
    ``apps.billing``. ``total_income`` is the net figure for the filtered set;
    ``payment_count`` counts qualifying payments while ``refund_count`` and
    ``total_refunds`` expose the refund side. ``by_payment_method`` and
    ``by_payment_type`` break the same filtered set down by net contribution,
    so their totals always sum back to ``total_income``.
    """
    filters = _income_filters(date_from, date_to, payment_method, payment_type)
    qs = CustomerPayment.objects.filter(**filters)

    gross = _decimal_sum(
        qs.exclude(payment_type=CustomerPayment.PaymentType.REFUND), "amount"
    )
    refunds = _decimal_sum(
        qs.filter(payment_type=CustomerPayment.PaymentType.REFUND), "amount"
    )

    net_expression = Case(
        When(
            payment_type=CustomerPayment.PaymentType.REFUND,
            then=-F("amount"),
        ),
        default=F("amount"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    refund_filter = Q(payment_type=CustomerPayment.PaymentType.REFUND)

    by_payment_method = []
    method_rows = (
        qs.values("payment_method")
        .annotate(
            total=Sum(net_expression),
            count=Count("id", filter=~refund_filter),
        )
        .order_by("-total")
    )
    for row in method_rows:
        by_payment_method.append(
            {
                "payment_method": row["payment_method"],
                "payment_method_display": CustomerPayment.Method(
                    row["payment_method"]
                ).label,
                "total": round(row["total"] or Decimal("0.00"), 2),
                "count": row["count"],
            }
        )

    by_payment_type = []
    type_rows = (
        qs.values("payment_type")
        .annotate(total=Sum(net_expression), count=Count("id"))
        .order_by("-total")
    )
    for row in type_rows:
        by_payment_type.append(
            {
                "payment_type": row["payment_type"],
                "payment_type_display": CustomerPayment.PaymentType(
                    row["payment_type"]
                ).label,
                "total": round(row["total"] or Decimal("0.00"), 2),
                "count": row["count"],
            }
        )

    return {
        "success": True,
        "total_income": round(gross - refunds, 2),
        "payment_count": qs.exclude(
            payment_type=CustomerPayment.PaymentType.REFUND
        ).count(),
        "refund_count": qs.filter(
            payment_type=CustomerPayment.PaymentType.REFUND
        ).count(),
        "total_refunds": round(refunds, 2),
        "by_payment_method": by_payment_method,
        "by_payment_type": by_payment_type,
    }


def build_expense_summary(
    date_from=None, date_to=None, category=None, payment_method=None
):
    """Expense summary over an inclusive date range, server-side derived.

    ``total_expenses`` and ``expense_count`` are the aggregate totals for the
    filtered set; ``by_category`` and ``by_payment_method`` break the totals
    down by controlled choice. All arithmetic stays in ``Decimal`` and is
    rounded to two places for the API.
    """
    filters = _range_kwargs(date_from, date_to, "expense_date")
    if category:
        filters["category"] = category
    if payment_method:
        filters["payment_method"] = payment_method

    qs = Expense.objects.filter(**filters)
    total = _decimal_sum(qs, "amount")
    count = qs.count()

    by_category = []
    category_rows = (
        qs.values("category").annotate(total=Sum("amount"), count=Count("id"))
    ).order_by("-total")
    for row in category_rows:
        by_category.append(
            {
                "category": row["category"],
                "category_display": Expense.Category(row["category"]).label,
                "total": round(row["total"] or Decimal("0.00"), 2),
                "count": row["count"],
            }
        )

    by_payment_method = []
    method_rows = (
        qs.values("payment_method").annotate(total=Sum("amount"), count=Count("id"))
    ).order_by("-total")
    for row in method_rows:
        by_payment_method.append(
            {
                "payment_method": row["payment_method"],
                "payment_method_display": Expense.Method(row["payment_method"]).label,
                "total": round(row["total"] or Decimal("0.00"), 2),
                "count": row["count"],
            }
        )

    return {
        "success": True,
        "total_expenses": round(total, 2),
        "expense_count": count,
        "by_category": by_category,
        "by_payment_method": by_payment_method,
    }


def build_reports_summary(date_from=None, date_to=None):
    """Read-only reports & business-insights summary over an inclusive range.

    Reports never become a second source of truth: income and expenses reuse
    the authoritative ``build_income_summary`` / ``build_expense_summary``
    aggregations verbatim (so the reports always agree with the income and
    expense management pages), and the net position is computed server-side
    from those values without storing a new financial record.

    Date filters apply consistently to every date-based metric:
    - orders by ``order_date`` (counts, status distribution, revenue, garments)
    - customer activity by order date / creation date
    - income and refunds by ``payment_date``
    - expenses by ``expense_date``
    - payroll paid by ``payment_date`` and salary advances by ``advance_date``

    Workload and active counts are live shop snapshots (same semantics as the
    dashboard) and are not date-filtered.
    """
    income = build_income_summary(date_from, date_to)
    income.pop("success", None)
    expenses = build_expense_summary(date_from, date_to)
    expenses.pop("success", None)

    order_filters = _range_kwargs(date_from, date_to, "order_date")
    orders = Order.objects.filter(**order_filters)

    order_counts = {status: 0 for status in OrderStatus.values}
    order_counts["total"] = orders.count()
    for row in orders.values("status").annotate(count=Count("id")):
        order_counts[row["status"]] = row["count"]

    order_revenue = _decimal_sum(orders, "total_amount")

    garment_quantities = {code: 0 for code in GarmentType.values}
    item_rows = (
        OrderItem.objects.filter(order__in=orders.values("id"))
        .values("garment_type")
        .annotate(total=Sum("quantity"))
    )
    for row in item_rows:
        garment_quantities[row["garment_type"]] = int(row["total"] or 0)

    customer_created_filters = _range_kwargs(date_from, date_to, "created_at__date")

    payroll_filters = _range_kwargs(date_from, date_to, "payment_date")
    advance_filters = _range_kwargs(date_from, date_to, "advance_date")

    return {
        "success": True,
        "range": {"date_from": date_from, "date_to": date_to},
        "orders": {
            "total": order_counts["total"],
            "status_distribution": order_counts,
            "revenue": round(order_revenue, 2),
            "garment_quantities": garment_quantities,
        },
        "customers": {
            "active_customers": Customer.objects.filter(is_active=True).count(),
            "new_customers": Customer.objects.filter(
                **customer_created_filters
            ).count(),
            "customers_with_orders": (
                Order.objects.filter(**order_filters)
                .values("customer_id")
                .distinct()
                .count()
            ),
        },
        "tailors": {
            "active_tailors": Tailor.objects.filter(is_active=True).count(),
            "workload": _workload_totals(),
        },
        "financial": {
            "income": income,
            "expenses": expenses,
            "net_position": round(
                income["total_income"] - expenses["total_expenses"], 2
            ),
            "payroll_paid": round(
                _decimal_sum(
                    PayrollPayment.objects.filter(**payroll_filters), "amount"
                ),
                2,
            ),
            "salary_advances": round(
                _decimal_sum(SalaryAdvance.objects.filter(**advance_filters), "amount"),
                2,
            ),
            "order_revenue": round(order_revenue, 2),
        },
    }
