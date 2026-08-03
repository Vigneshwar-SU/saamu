"""Payroll API views.

Permission model (backend authoritative, same as attendance/tailors):
- Reads (period list/detail, entries, tailor detail) -> OWNER or STAFF.
- Mutations (create period, calculate, finalize) -> STAFF.

Lifecycle: periods are created as DRAFT, ``calculate`` populates entries and
moves the period to CALCULATED (re-runnable while editable), and ``finalize``
moves CALCULATED periods to FINALIZED (immutable through normal operations).
"""

from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.tailors.models import Tailor, WorkAssignment

from .models import PayrollEntry, PayrollPeriod
from .serializers import (
    PayrollAssignmentSerializer,
    PayrollEntrySerializer,
    PayrollPeriodSerializer,
)

PAYROLL_PERIOD_MUTATION_ACTIONS = {"create", "calculate", "finalize"}


class PayrollPeriodViewSet(viewsets.ModelViewSet):
    """Payroll periods with DRAFT -> CALCULATED -> FINALIZED lifecycle."""

    http_method_names = ["get", "post", "head", "options"]
    serializer_class = PayrollPeriodSerializer
    queryset = PayrollPeriod.objects.select_related("created_by").all()

    def get_permissions(self):
        if self.action in PAYROLL_PERIOD_MUTATION_ACTIONS:
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="calculate")
    def calculate(self, request, pk=None):
        """Aggregate piece-rate earnings + attendance into payroll entries.

        Replaces existing entries and moves the period to CALCULATED. Rejected
        for FINALIZED periods (immutable through normal operations).
        """
        period = self.get_object()
        if period.status == PayrollPeriod.Status.FINALIZED:
            raise ValidationError(
                {
                    "detail": (
                        "Finalized payroll periods cannot be recalculated. "
                        "Finalization is irreversible."
                    )
                }
            )
        period.calculate()
        entries = period.entries.select_related("tailor").all()
        return Response(
            {
                "success": True,
                "message": "Payroll period calculated successfully.",
                "period": PayrollPeriodSerializer(
                    period, context=self.get_serializer_context()
                ).data,
                "entries": PayrollEntrySerializer(
                    entries, many=True, context=self.get_serializer_context()
                ).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize(self, request, pk=None):
        """Mark a calculated period as FINALIZED (immutable)."""
        period = self.get_object()
        if period.status == PayrollPeriod.Status.FINALIZED:
            raise ValidationError(
                {"detail": "This payroll period is already finalized."}
            )
        if period.status != PayrollPeriod.Status.CALCULATED:
            raise ValidationError(
                {"detail": ("Calculate the payroll period before finalizing it.")}
            )
        period.status = PayrollPeriod.Status.FINALIZED
        period.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "success": True,
                "message": "Payroll period finalized successfully.",
                "period": PayrollPeriodSerializer(
                    period, context=self.get_serializer_context()
                ).data,
            }
        )

    @action(
        detail=True,
        methods=["get"],
        url_path=r"tailors/(?P<tailor_id>[^/.]+)",
    )
    def tailor_detail(self, request, pk=None, tailor_id=None):
        """Payroll summary and assignment earning breakdown for one tailor."""
        period = self.get_object()
        tailor = get_object_or_404(Tailor, pk=tailor_id)
        entry = period.entries.filter(tailor=tailor).first()
        assignments = (
            WorkAssignment.objects.filter(
                tailor=tailor,
                status=WorkAssignment.Status.COMPLETED,
                completed_at__date__gte=period.period_start,
                completed_at__date__lte=period.period_end,
            )
            .select_related("order_item", "order_item__order")
            .order_by("completed_at", "id")
        )
        context = self.get_serializer_context()
        return Response(
            {
                "success": True,
                "period": PayrollPeriodSerializer(period, context=context).data,
                "tailor": {
                    "id": tailor.id,
                    "name": tailor.full_name,
                    "mobile_number": tailor.mobile_number,
                    "is_active": tailor.is_active,
                },
                "entry": (
                    PayrollEntrySerializer(entry, context=context).data
                    if entry
                    else None
                ),
                "assignments": PayrollAssignmentSerializer(
                    assignments, many=True, context=context
                ).data,
            }
        )


class PayrollEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only payroll entries with ``period`` / ``tailor`` filters."""

    serializer_class = PayrollEntrySerializer
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        qs = PayrollEntry.objects.select_related("payroll_period", "tailor").all()
        period = (self.request.query_params.get("period") or "").strip()
        if period:
            qs = qs.filter(payroll_period_id=period)
        tailor = (self.request.query_params.get("tailor") or "").strip()
        if tailor:
            qs = qs.filter(tailor_id=tailor)
        return qs
