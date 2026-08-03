"""Income, expense and dashboard API views.

Permission model (backend authoritative):
- Reads (list/detail) -> OWNER or STAFF.
- Mutations (create) -> STAFF.

Income and expense records are financial history: they are never updated or
deleted (no update/delete routes). List filtering supports ``date_from``,
``date_to`` and ``category`` with inclusive date boundaries. The dashboard is
read-only for OWNER + STAFF and never mutates source data.
"""

from datetime import date

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole

from .models import Expense, Income
from .serializers import ExpenseSerializer, IncomeSerializer
from .services import build_dashboard_summary


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


class IncomeViewSet(viewsets.ModelViewSet):
    """Income records with OWNER+STAFF reads and STAFF creation."""

    http_method_names = ["get", "post", "head", "options"]
    serializer_class = IncomeSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_queryset(self):
        qs = Income.objects.select_related("recorded_by").all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        date_from, date_to = _parse_range(self.request)
        if date_from:
            qs = qs.filter(income_date__gte=date_from)
        if date_to:
            qs = qs.filter(income_date__lte=date_to)

        category = (self.request.query_params.get("category") or "").strip()
        if category:
            if category not in Income.Category.values:
                raise ValidationError({"category": "Invalid income category filter."})
            qs = qs.filter(category=category)

        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


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

        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class DashboardSummaryView(APIView):
    """Read-only dashboard: financial + operational summary over a date range."""

    permission_classes = [IsOwnerOrStaff]

    def get(self, request):
        date_from, date_to = _parse_range(request)
        return Response(build_dashboard_summary(date_from, date_to, request=request))
