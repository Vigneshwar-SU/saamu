"""Salary advance API views.

Permission model (backend authoritative):
- Reads (list/detail) -> OWNER or STAFF.
- Mutations (create) -> STAFF.

Advances are financial history and are never deleted (no update/delete routes).
List filtering supports ``tailor``, ``status``, ``date_from`` and ``date_to``;
the full record set (including archived tailors) remains retrievable.
"""

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.common.pagination import SaamuPageNumberPagination

from .models import SalaryAdvance
from .serializers import SalaryAdvanceSerializer


class SalaryAdvanceViewSet(viewsets.ModelViewSet):
    """Salary advances with OWNER+STAFF reads and STAFF creation."""

    http_method_names = ["get", "post", "head", "options"]
    serializer_class = SalaryAdvanceSerializer
    pagination_class = SaamuPageNumberPagination

    def get_permissions(self):
        if self.action == "create":
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_queryset(self):
        qs = SalaryAdvance.objects.select_related("tailor", "recorded_by").all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        tailor = (self.request.query_params.get("tailor") or "").strip()
        if tailor:
            qs = qs.filter(tailor_id=tailor)

        status = (self.request.query_params.get("status") or "").strip()
        if status:
            if status not in SalaryAdvance.Status.values:
                raise ValidationError({"status": "Invalid advance status filter."})
            qs = qs.filter(status=status)

        date_from = (self.request.query_params.get("date_from") or "").strip()
        if date_from:
            qs = qs.filter(advance_date__gte=date_from)

        date_to = (self.request.query_params.get("date_to") or "").strip()
        if date_to:
            qs = qs.filter(advance_date__lte=date_to)

        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
