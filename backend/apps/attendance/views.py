"""Attendance API views.

Permission model (backend authoritative, same as tailors/customers):
- Reads (list/detail) -> OWNER or STAFF.
- Mutations (create, safe PATCH) -> STAFF.

Attendance records are never deleted. List filtering supports ``tailor``,
``date_from``, ``date_to`` and ``status``; the full record set (including
archived tailors) remains retrievable.
"""

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.attendance.models import Attendance
from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.common.pagination import SaamuPageNumberPagination

from .serializers import AttendanceSerializer

ATTENDANCE_MUTATION_ACTIONS = {"create", "partial_update"}


class AttendanceViewSet(viewsets.ModelViewSet):
    """Daily tailor attendance with OWNER+STAFF reads and STAFF mutations."""

    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = AttendanceSerializer
    pagination_class = SaamuPageNumberPagination

    def get_permissions(self):
        if self.action in ATTENDANCE_MUTATION_ACTIONS:
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_queryset(self):
        qs = Attendance.objects.select_related("tailor", "marked_by").all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        tailor = (self.request.query_params.get("tailor") or "").strip()
        if tailor:
            qs = qs.filter(tailor_id=tailor)

        date_from = (self.request.query_params.get("date_from") or "").strip()
        if date_from:
            qs = qs.filter(attendance_date__gte=date_from)

        date_to = (self.request.query_params.get("date_to") or "").strip()
        if date_to:
            qs = qs.filter(attendance_date__lte=date_to)

        status = (self.request.query_params.get("status") or "").strip()
        if status:
            if status not in Attendance.Status.values:
                raise ValidationError({"status": "Invalid attendance status filter."})
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(marked_by=self.request.user)
