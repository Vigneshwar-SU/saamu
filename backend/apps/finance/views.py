"""Income, expense and dashboard API views.

Permission model (backend authoritative):
- Reads (list/detail) -> OWNER or STAFF.
- Mutations (create) -> STAFF (expenses only).

Income (Phase 13) is never mutated here: it is derived read-only from the
append-only customer payments recorded through the billing API, so income
viewing can never bypass billing permissions or accept client-supplied totals.
The income list supports ``date_from``, ``date_to``, ``payment_method`` and
``payment_type`` filters with inclusive date boundaries, and
``GET /income/summary/`` returns server-side derived totals and breakdowns
honoring the same filters. Expense records are financial history with no
update/delete routes. The dashboard is read-only for OWNER + STAFF and never
mutates source data.
"""

from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.billing.models import CustomerPayment

from .models import Expense
from .serializers import ExpenseSerializer, IncomeSerializer
from .services import (
    build_dashboard_summary,
    build_expense_summary,
    build_income_summary,
    build_reports_summary,
)


def _parse_date(value, field_name):
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise ValidationError({field_name: "Enter a valid date (YYYY-MM-DD)."})


def _parse_range(request):
    """Parse and validate the inclusive date_from/date_to query range."""
    date_from = _parse_date(request.query_params.get("date_from"), "date_from")
    date_to = _parse_date(request.query_params.get("date_to"), "date_to")
    if date_from and date_to and date_to < date_from:
        raise ValidationError({"date_to": "date_to cannot be earlier than date_from."})
    return date_from, date_to


class IncomeViewSet(viewsets.ReadOnlyModelViewSet):
    """Customer-derived income records, read-only for OWNER and STAFF.

    Income is derived from append-only customer payments: each payment
    contributes to income exactly once and REFUND transactions reduce net
    income. Recording or editing a payment is only ever possible through the
    billing API, so this view exposes no mutation surface.
    """

    serializer_class = IncomeSerializer

    def get_permissions(self):
        return [IsOwnerOrStaff()]

    def get_queryset(self):
        qs = CustomerPayment.objects.select_related(
            "invoice__order__customer", "recorded_by"
        ).all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        date_from, date_to = _parse_range(self.request)
        if date_from:
            qs = qs.filter(payment_date__gte=date_from)
        if date_to:
            qs = qs.filter(payment_date__lte=date_to)

        payment_method = (self.request.query_params.get("payment_method") or "").strip()
        if payment_method:
            if payment_method not in CustomerPayment.Method.values:
                raise ValidationError(
                    {"payment_method": "Invalid payment method filter."}
                )
            qs = qs.filter(payment_method=payment_method)

        payment_type = (self.request.query_params.get("payment_type") or "").strip()
        if payment_type:
            if payment_type not in CustomerPayment.PaymentType.values:
                raise ValidationError({"payment_type": "Invalid payment type filter."})
            qs = qs.filter(payment_type=payment_type)

        return qs

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Server-side income summary honoring the same list filters.

        ``total_income`` is net customer-derived income (qualifying payments
        minus refunds) for an inclusive date range; ``by_payment_method`` and
        ``by_payment_type`` break the filtered set down so their totals sum
        back to ``total_income``.
        """
        date_from, date_to = _parse_range(request)
        payment_method = (request.query_params.get("payment_method") or "").strip()
        if payment_method and payment_method not in CustomerPayment.Method.values:
            raise ValidationError({"payment_method": "Invalid payment method filter."})

        payment_type = (request.query_params.get("payment_type") or "").strip()
        if payment_type and payment_type not in CustomerPayment.PaymentType.values:
            raise ValidationError({"payment_type": "Invalid payment type filter."})

        return Response(
            build_income_summary(
                date_from,
                date_to,
                payment_method=payment_method or None,
                payment_type=payment_type or None,
            )
        )


class ExpenseViewSet(viewsets.ModelViewSet):
    """Expense records with OWNER+STAFF reads and STAFF creation."""

    http_method_names = ["get", "post", "head", "options"]
    serializer_class = ExpenseSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_queryset(self):
        qs = Expense.objects.select_related("recorded_by").all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        date_from, date_to = _parse_range(self.request)
        if date_from:
            qs = qs.filter(expense_date__gte=date_from)
        if date_to:
            qs = qs.filter(expense_date__lte=date_to)

        category = (self.request.query_params.get("category") or "").strip()
        if category:
            if category not in Expense.Category.values:
                raise ValidationError({"category": "Invalid expense category filter."})
            qs = qs.filter(category=category)

        payment_method = (self.request.query_params.get("payment_method") or "").strip()
        if payment_method:
            if payment_method not in Expense.Method.values:
                raise ValidationError(
                    {"payment_method": "Invalid payment method filter."}
                )
            qs = qs.filter(payment_method=payment_method)

        return qs

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Server-side expense summary honoring the same list filters.

        Returns total expenses, expense count and per-category / per-payment-
        method breakdowns for an inclusive date range. Read-only for OWNER and
        STAFF; every figure is derived from database records.
        """
        date_from, date_to = _parse_range(request)
        category = (request.query_params.get("category") or "").strip()
        if category and category not in Expense.Category.values:
            raise ValidationError({"category": "Invalid expense category filter."})

        payment_method = (request.query_params.get("payment_method") or "").strip()
        if payment_method and payment_method not in Expense.Method.values:
            raise ValidationError({"payment_method": "Invalid payment method filter."})

        return Response(
            build_expense_summary(
                date_from,
                date_to,
                category=category or None,
                payment_method=payment_method or None,
            )
        )

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class DashboardSummaryView(APIView):
    """Read-only dashboard: financial + operational summary over a date range."""

    permission_classes = [IsOwnerOrStaff]

    def get(self, request):
        date_from, date_to = _parse_range(request)
        return Response(build_dashboard_summary(date_from, date_to, request=request))


class ReportsSummaryView(APIView):
    """Read-only reports & business insights summary over a date range.

    All values are aggregated server-side from the authoritative records:
    income/refunds from ``CustomerPayment`` (Phase 13), expenses from
    ``Expense`` (Phase 12), and orders / customers / workload from their own
    modules. The net position is derived, never stored. Only ``GET`` is
    allowed, so reports can never mutate business records.
    """

    permission_classes = [IsOwnerOrStaff]

    def get(self, request):
        date_from, date_to = _parse_range(request)
        return Response(build_reports_summary(date_from, date_to))
