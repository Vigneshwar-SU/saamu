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
from apps.payments.models import PayrollPayment, SalaryAdvance
from apps.payments.serializers import (
    PayrollPaymentCreateSerializer,
    PayrollPaymentSerializer,
    SalaryAdvanceSerializer,
)
from apps.payments.services import (
    apply_advance,
    record_payment,
    settle_entry,
    settlement_summary,
)
from apps.tailors.models import Tailor, WorkAssignment

from .models import PayrollEntry, PayrollPeriod
from .serializers import (
    PayrollAssignmentSerializer,
    PayrollEntrySerializer,
    PayrollPeriodSerializer,
)

PAYROLL_PERIOD_MUTATION_ACTIONS = {"create", "calculate", "finalize"}

SETTLEMENT_MUTATION_ACTIONS = {"payments", "settle", "apply_advance"}


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
    """Read-only payroll entries plus settlement sub-resources.

    The ``settlement``, ``payments``, ``settle`` and ``apply-advance`` actions
    let OWNER/STAFF view derived settlement values and STAFF record payments,
    apply advances and settle entries. All mutation logic lives in
    ``apps.payments.services`` and is concurrency-safe.
    """

    serializer_class = PayrollEntrySerializer
    permission_classes = [IsOwnerOrStaff]

    def get_permissions(self):
        if self.action in SETTLEMENT_MUTATION_ACTIONS and self.request.method == "POST":
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_queryset(self):
        qs = PayrollEntry.objects.select_related("payroll_period", "tailor").all()
        period = (self.request.query_params.get("period") or "").strip()
        if period:
            qs = qs.filter(payroll_period_id=period)
        tailor = (self.request.query_params.get("tailor") or "").strip()
        if tailor:
            qs = qs.filter(tailor_id=tailor)
        return qs

    @action(detail=True, methods=["get"], url_path="settlement")
    def settlement(self, request, pk=None):
        """Derived settlement summary (gross, deductions, paid, outstanding)."""
        entry = self.get_object()
        return Response(
            {
                "success": True,
                "entry": PayrollEntrySerializer(
                    entry, context=self.get_serializer_context()
                ).data,
                "settlement": settlement_summary(entry),
            }
        )

    @action(detail=True, methods=["get", "post"], url_path="payments")
    def payments(self, request, pk=None):
        """Payment history (GET) or record a payment (POST, STAFF)."""
        entry = self.get_object()
        if request.method == "GET":
            payments = PayrollPayment.objects.filter(
                payroll_entry=entry
            ).select_related("tailor", "recorded_by")
            return Response(
                {
                    "success": True,
                    "entry_id": entry.id,
                    "payments": PayrollPaymentSerializer(
                        payments, many=True, context=self.get_serializer_context()
                    ).data,
                }
            )

        serializer = PayrollPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment, settlement = record_payment(
            entry=entry,
            amount=data["amount"],
            payment_date=data["payment_date"],
            payment_method=data["payment_method"],
            reference=data.get("reference", ""),
            notes=data.get("notes", ""),
            recorded_by=request.user,
        )
        return Response(
            {
                "success": True,
                "message": "Payment recorded successfully.",
                "payment": PayrollPaymentSerializer(
                    payment, context=self.get_serializer_context()
                ).data,
                "settlement": settlement,
            },
            status=http_status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="settle")
    def settle(self, request, pk=None):
        """Explicit full settlement: one payment covering the outstanding."""
        serializer = PayrollPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment, settlement = settle_entry(
            entry=self.get_object(),
            payment_date=data["payment_date"],
            payment_method=data["payment_method"],
            reference=data.get("reference", ""),
            notes=data.get("notes", ""),
            recorded_by=request.user,
        )
        return Response(
            {
                "success": True,
                "message": "Payroll entry settled in full.",
                "payment": PayrollPaymentSerializer(
                    payment, context=self.get_serializer_context()
                ).data,
                "settlement": settlement,
            }
        )

    @action(detail=True, methods=["post"], url_path="apply-advance")
    def apply_advance(self, request, pk=None):
        """Deduct an OUTSTANDING advance against this payroll entry."""
        entry = self.get_object()
        advance_id = request.data.get("advance_id")
        if not advance_id:
            raise ValidationError({"advance_id": "advance_id is required."})
        advance = get_object_or_404(SalaryAdvance, pk=advance_id)
        advance, settlement = apply_advance(
            entry=entry, advance=advance, recorded_by=request.user
        )
        return Response(
            {
                "success": True,
                "message": "Advance applied to the payroll entry.",
                "advance": SalaryAdvanceSerializer(
                    advance, context=self.get_serializer_context()
                ).data,
                "settlement": settlement,
            }
        )
