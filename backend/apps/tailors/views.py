"""Tailors, piece rates, work assignments and earnings views.

Permission model (backend authoritative, same as customers/orders):
- Reads (list/detail/earnings/summary) -> OWNER or STAFF.
- Mutations (create, safe PATCH, archive/restore, status transitions) -> STAFF.

Work assignment integrity:
- Assignments only for active tailors and existing order items.
- ``assigned_quantity`` is checked against the item's remaining quantity under a
  row lock so concurrent assignments never over-allocate.
- The applicable piece rate is snapshotted at assignment time; later rate edits
  never rewrite history.
- Status follows ASSIGNED -> IN_PROGRESS -> COMPLETED; completed work cannot be
  reopened and completed quantity can never exceed assigned quantity.
"""

from django.db import models, transaction
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.customers.models import GarmentType
from apps.orders.models import OrderItem

from .models import PieceRate, Tailor, WorkAssignment
from .serializers import (
    PieceRateSerializer,
    TailorSerializer,
    WorkAssignmentCreateSerializer,
    WorkAssignmentSerializer,
)

TAILOR_MUTATION_ACTIONS = {"create", "partial_update", "archive", "restore"}
PIECE_RATE_MUTATION_ACTIONS = {"create", "partial_update"}
WORK_ASSIGNMENT_MUTATION_ACTIONS = {"create", "partial_update", "change_status"}


def _earnings_for_queryset(qs):
    """Aggregate completed quantity and earnings for a queryset.

    Returns a dict with totals plus a per-garment breakdown keyed by the raw
    garment type code. Assignments that were never completed contribute zero.
    """
    completed = qs.filter(status=WorkAssignment.Status.COMPLETED)
    totals = {"total_completed_quantity": 0, "total_earned": 0}
    breakdown = {}
    for assignment in completed:
        amount = assignment.completed_quantity * assignment.rate_per_piece_snapshot
        totals["total_completed_quantity"] += assignment.completed_quantity
        totals["total_earned"] += amount
        code = assignment.order_item.garment_type
        entry = breakdown.setdefault(
            code, {"garment_type": code, "completed_quantity": 0, "earned_amount": 0}
        )
        entry["completed_quantity"] += assignment.completed_quantity
        entry["earned_amount"] += amount
    totals["total_earned"] = round(totals["total_earned"], 2)
    totals["total_completed_quantity"] = int(totals["total_completed_quantity"])
    for entry in breakdown.values():
        entry["earned_amount"] = round(entry["earned_amount"], 2)
        entry["completed_quantity"] = int(entry["completed_quantity"])
    return totals, sorted(breakdown.values(), key=lambda e: e["garment_type"])


def _workload_for_queryset(qs):
    """Aggregate assigned/completed/outstanding pieces and piece-rate earnings.

    Unlike ``_earnings_for_queryset`` (which only counts COMPLETED
    assignments), this aggregates across every assignment so partially
    completed work stays visible as workload progress. Per assignment:
    ``outstanding = assigned - completed`` and
    ``earned = completed * rate_per_piece_snapshot`` (incomplete pieces never
    count as earned).

    Returns ``(totals, per_tailor)`` with four workload figures each, where
    ``per_tailor`` is keyed by tailor id.
    """

    totals = {
        "assigned_quantity": 0,
        "completed_quantity": 0,
        "outstanding_quantity": 0,
        "earned_amount": 0,
    }
    per_tailor = {}
    for assignment in qs:
        outstanding = max(
            assignment.assigned_quantity - assignment.completed_quantity, 0
        )
        earned = assignment.completed_quantity * assignment.rate_per_piece_snapshot
        totals["assigned_quantity"] += assignment.assigned_quantity
        totals["completed_quantity"] += assignment.completed_quantity
        totals["outstanding_quantity"] += outstanding
        totals["earned_amount"] += earned
        entry = per_tailor.setdefault(
            assignment.tailor_id,
            {
                "assigned_quantity": 0,
                "completed_quantity": 0,
                "outstanding_quantity": 0,
                "earned_amount": 0,
            },
        )
        entry["assigned_quantity"] += assignment.assigned_quantity
        entry["completed_quantity"] += assignment.completed_quantity
        entry["outstanding_quantity"] += outstanding
        entry["earned_amount"] += earned

    totals["earned_amount"] = round(totals["earned_amount"], 2)
    for key in ("assigned_quantity", "completed_quantity", "outstanding_quantity"):
        totals[key] = int(totals[key])
    for entry in per_tailor.values():
        entry["earned_amount"] = round(entry["earned_amount"], 2)
        for key in ("assigned_quantity", "completed_quantity", "outstanding_quantity"):
            entry[key] = int(entry[key])
    return totals, per_tailor


class TailorViewSet(viewsets.ModelViewSet):
    """Tailor profile CRUD with archive/restore and per-tailor earnings."""

    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = TailorSerializer

    def get_permissions(self):
        if self.action in TAILOR_MUTATION_ACTIONS:
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_queryset(self):
        qs = Tailor.objects.all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        """Search by name/mobile plus active/archived/all scope.

        ``?scope=active`` (default) | ``scope=archived`` | ``scope=all``.
        """
        scope = (self.request.query_params.get("scope") or "active").strip()
        if scope not in {"active", "archived", "all"}:
            raise ValidationError(
                {"scope": "Invalid scope. Use active, archived or all."}
            )
        if scope == "active":
            qs = qs.filter(is_active=True)
        elif scope == "archived":
            qs = qs.filter(is_active=False)

        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                models.Q(full_name__icontains=search)
                | models.Q(mobile_number__icontains=search)
            )
        return qs

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """Archive a tailor. Archived tailors can no longer receive assignments
        but their historical work stays intact."""
        tailor = self.get_object()
        if not tailor.is_active:
            raise ValidationError({"detail": "This tailor is already archived."})
        tailor.is_active = False
        tailor.save(update_fields=["is_active", "updated_at"])
        return Response(
            {
                "success": True,
                "message": f"{tailor.full_name} has been archived.",
                "tailor": TailorSerializer(
                    tailor, context=self.get_serializer_context()
                ).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """Restore an archived tailor so they can receive new assignments again."""
        tailor = self.get_object()
        if tailor.is_active:
            raise ValidationError({"detail": "This tailor is already active."})
        tailor.is_active = True
        tailor.save(update_fields=["is_active", "updated_at"])
        return Response(
            {
                "success": True,
                "message": f"{tailor.full_name} has been restored.",
                "tailor": TailorSerializer(
                    tailor, context=self.get_serializer_context()
                ).data,
            }
        )

    @action(detail=True, methods=["get"], url_path="earnings")
    def earnings(self, request, pk=None):
        """Earnings summary for one tailor.

        Filters: ``?date_from=`` / ``?date_to=`` (on completed_at), optional
        ``?garment_type=``. Only completed assignments contribute to earnings.
        """
        tailor = self.get_object()
        qs = tailor.work_assignments.select_related("order_item", "order_item__order")
        qs = self._apply_earnings_filters(qs)
        totals, breakdown = _earnings_for_queryset(qs)
        workload, _ = _workload_for_queryset(tailor.work_assignments.all())
        return Response(
            {
                "success": True,
                "tailor": TailorSerializer(
                    tailor, context=self.get_serializer_context()
                ).data,
                "summary": totals,
                "garment_breakdown": breakdown,
                "workload": workload,
            }
        )

    def _apply_earnings_filters(self, qs):
        date_from = (self.request.query_params.get("date_from") or "").strip()
        if date_from:
            qs = qs.filter(completed_at__date__gte=date_from)
        date_to = (self.request.query_params.get("date_to") or "").strip()
        if date_to:
            qs = qs.filter(completed_at__date__lte=date_to)
        garment = (self.request.query_params.get("garment_type") or "").strip()
        if garment:
            if garment not in GarmentType.values:
                raise ValidationError({"garment_type": "Invalid garment type filter."})
            qs = qs.filter(order_item__garment_type=garment)
        return qs


class TailorEarningsSummaryView(APIView):
    """Aggregate earnings across tailors.

    Filters: ``?date_from=`` / ``?date_to=`` (on completed_at), ``?tailor=``.
    Returns a per-tailor summary plus grand totals. Reads only (OWNER+STAFF).
    """

    permission_classes = [IsOwnerOrStaff]

    def get(self, request):
        qs = (
            WorkAssignment.objects.select_related(
                "tailor", "order_item", "order_item__order"
            )
            .filter(status=WorkAssignment.Status.COMPLETED)
            .order_by("-completed_at")
        )

        tailor_id = (request.query_params.get("tailor") or "").strip()
        if tailor_id:
            if not Tailor.objects.filter(pk=tailor_id).exists():
                raise ValidationError({"tailor": "Tailor not found."})
            qs = qs.filter(tailor_id=tailor_id)

        date_from = (request.query_params.get("date_from") or "").strip()
        if date_from:
            qs = qs.filter(completed_at__date__gte=date_from)
        date_to = (request.query_params.get("date_to") or "").strip()
        if date_to:
            qs = qs.filter(completed_at__date__lte=date_to)

        totals = {"total_completed_quantity": 0, "total_earned": 0}
        per_tailor = {}
        for assignment in qs:
            amount = assignment.completed_quantity * assignment.rate_per_piece_snapshot
            totals["total_completed_quantity"] += assignment.completed_quantity
            totals["total_earned"] += amount
            entry = per_tailor.setdefault(
                assignment.tailor_id,
                {
                    "id": assignment.tailor_id,
                    "name": assignment.tailor.full_name,
                    "completed_quantity": 0,
                    "earned_amount": 0,
                    "outstanding_quantity": 0,
                },
            )
            entry["completed_quantity"] += assignment.completed_quantity
            entry["earned_amount"] += amount

        # Outstanding workload: sum of (assigned - completed) over all
        # assignments that are not yet COMPLETED.
        outstanding = (
            WorkAssignment.objects.exclude(status=WorkAssignment.Status.COMPLETED)
            .values("tailor_id")
            .annotate(
                total=models.Sum(
                    models.F("assigned_quantity") - models.F("completed_quantity")
                )
            )
        )
        for row in outstanding:
            entry = per_tailor.get(row["tailor_id"])
            if entry is None:
                tailor = Tailor.objects.filter(pk=row["tailor_id"]).first()
                if tailor is None:
                    continue
                entry = per_tailor.setdefault(
                    row["tailor_id"],
                    {
                        "id": row["tailor_id"],
                        "name": tailor.full_name,
                        "completed_quantity": 0,
                        "earned_amount": 0,
                        "outstanding_quantity": 0,
                    },
                )
            entry["outstanding_quantity"] = int(row["total"] or 0)

        # Workload overview: aggregate assigned/completed/outstanding/earned
        # across ALL assignments (including partially completed work), not just
        # COMPLETED ones. The optional ``tailor`` filter is honored so the
        # summary can be scoped to a single tailor.
        workload_qs = WorkAssignment.objects.select_related("tailor").all()
        if tailor_id:
            workload_qs = workload_qs.filter(tailor_id=tailor_id)
        workload_totals, workload_by_tailor = _workload_for_queryset(workload_qs)
        totals["total_active_tailors"] = Tailor.objects.filter(is_active=True).count()
        totals["workload"] = {
            "total_assigned": workload_totals["assigned_quantity"],
            "total_completed": workload_totals["completed_quantity"],
            "total_outstanding": workload_totals["outstanding_quantity"],
            "total_earned": workload_totals["earned_amount"],
        }
        for entry in per_tailor.values():
            wl = workload_by_tailor.get(entry["id"])
            if wl is None:
                wl = {
                    "assigned_quantity": 0,
                    "completed_quantity": 0,
                    "outstanding_quantity": 0,
                    "earned_amount": 0,
                }
            entry["workload"] = {
                "assigned_quantity": wl["assigned_quantity"],
                "completed_quantity": wl["completed_quantity"],
                "outstanding_quantity": wl["outstanding_quantity"],
                "earned_amount": wl["earned_amount"],
            }

        totals["total_earned"] = round(totals["total_earned"], 2)
        totals["total_completed_quantity"] = int(totals["total_completed_quantity"])
        for entry in per_tailor.values():
            entry["earned_amount"] = round(entry["earned_amount"], 2)
            entry["completed_quantity"] = int(entry["completed_quantity"])
        return Response(
            {
                "success": True,
                "summary": totals,
                "tailors": sorted(
                    per_tailor.values(), key=lambda e: -e["earned_amount"]
                ),
            }
        )


class PieceRateViewSet(viewsets.ModelViewSet):
    """Piece rates per garment type. Rates are never deleted; deactivated instead."""

    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = PieceRateSerializer
    queryset = PieceRate.objects.all()

    def get_permissions(self):
        if self.action in PIECE_RATE_MUTATION_ACTIONS:
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rate = serializer.save()
        return Response(
            PieceRateSerializer(rate, context=self.get_serializer_context()).data,
            status=http_status.HTTP_201_CREATED,
        )


class WorkAssignmentViewSet(viewsets.ModelViewSet):
    """Work assignments: assign order items to tailors and track progress."""

    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = WorkAssignmentSerializer

    def get_permissions(self):
        if self.action in WORK_ASSIGNMENT_MUTATION_ACTIONS:
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_serializer_class(self):
        if self.action == "create":
            return WorkAssignmentCreateSerializer
        return WorkAssignmentSerializer

    def get_queryset(self):
        qs = WorkAssignment.objects.select_related(
            "tailor", "order_item", "order_item__order", "order_item__order__customer"
        ).all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        tailor = (self.request.query_params.get("tailor") or "").strip()
        if tailor:
            qs = qs.filter(tailor_id=tailor)

        order = (self.request.query_params.get("order") or "").strip()
        if order:
            qs = qs.filter(order_item__order_id=order)

        garment = (self.request.query_params.get("garment_type") or "").strip()
        if garment:
            if garment not in GarmentType.values:
                raise ValidationError({"garment_type": "Invalid garment type filter."})
            qs = qs.filter(order_item__garment_type=garment)

        status_filter = (self.request.query_params.get("status") or "").strip()
        if status_filter:
            if status_filter not in WorkAssignment.Status.values:
                raise ValidationError({"status": "Invalid assignment status filter."})
            qs = qs.filter(status=status_filter)

        date_from = (self.request.query_params.get("date_from") or "").strip()
        if date_from:
            qs = qs.filter(assigned_at__date__gte=date_from)
        date_to = (self.request.query_params.get("date_to") or "").strip()
        if date_to:
            qs = qs.filter(assigned_at__date__lte=date_to)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order_item = data["order_item"]
        assigned_quantity = data["assigned_quantity"]

        rate = PieceRate.objects.filter(
            garment_type=order_item.garment_type, is_active=True
        ).first()
        if rate is None:
            raise ValidationError(
                {
                    "order_item": (
                        "No active piece rate is configured for this garment type. "
                        "Configure the piece rate before assigning work."
                    )
                }
            )

        with transaction.atomic():
            locked_item = OrderItem.objects.select_for_update().get(pk=order_item.pk)
            assigned_total = (
                locked_item.work_assignments.aggregate(
                    total=models.Sum("assigned_quantity")
                )["total"]
                or 0
            )
            remaining = locked_item.quantity - assigned_total
            if assigned_quantity > remaining:
                raise ValidationError(
                    {
                        "assigned_quantity": (
                            f"Only {remaining} of this garment remain unassigned "
                            f"(item quantity is {locked_item.quantity})."
                        )
                    }
                )
            assignment = WorkAssignment.objects.create(
                tailor=data["tailor"],
                order_item=locked_item,
                assigned_quantity=assigned_quantity,
                completed_quantity=0,
                rate_per_piece_snapshot=rate.rate_per_piece,
                created_by=request.user if request.user.is_authenticated else None,
            )

        return Response(
            WorkAssignmentSerializer(
                assignment, context=self.get_serializer_context()
            ).data,
            status=http_status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        """Safe operational update: report completed quantity (STAFF only).

        Completed quantity cannot exceed the assigned quantity and cannot be
        changed after the assignment is marked COMPLETED.
        """
        assignment = self.get_object()
        completed = request.data.get("completed_quantity")
        if completed is None:
            raise ValidationError({"completed_quantity": "This field is required."})
        if assignment.status == WorkAssignment.Status.COMPLETED:
            raise ValidationError(
                {
                    "completed_quantity": (
                        "This assignment is already COMPLETED and cannot be updated."
                    )
                }
            )
        serializer = self.get_serializer(
            assignment,
            data={"completed_quantity": completed},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["completed_quantity"] = min(
            serializer.validated_data["completed_quantity"],
            assignment.assigned_quantity,
        )
        assignment = serializer.save()
        return Response(
            WorkAssignmentSerializer(
                assignment, context=self.get_serializer_context()
            ).data
        )

    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, pk=None):
        """Transition an assignment: ASSIGNED -> IN_PROGRESS -> COMPLETED.

        Body: ``{"status": "IN_PROGRESS"}`` or
        ``{"status": "COMPLETED", "completed_quantity": N}``. Completing without
        an explicit quantity completes the full assigned quantity. Earnings are
        computed from ``completed_quantity * rate_snapshot``.
        """
        assignment = self.get_object()
        requested = (request.data.get("status") or "").strip()
        if requested not in WorkAssignment.Status.values:
            raise ValidationError({"status": "Invalid assignment status."})
        new_status = WorkAssignment.Status(requested)

        if new_status == WorkAssignment.Status.COMPLETED:
            completed = request.data.get("completed_quantity")
            completed_quantity = assignment.assigned_quantity
            if completed is not None:
                try:
                    completed_quantity = int(completed)
                except (TypeError, ValueError):
                    raise ValidationError(
                        {"completed_quantity": "Enter a valid whole number."}
                    )
                if (
                    completed_quantity < 0
                    or completed_quantity > assignment.assigned_quantity
                ):
                    raise ValidationError(
                        {
                            "completed_quantity": (
                                f"Completed quantity must be between 0 and "
                                f"{assignment.assigned_quantity} (the assigned quantity)."
                            )
                        }
                    )
            assignment.completed_quantity = completed_quantity

        advanced = assignment.advance_status(new_status)
        if not advanced:
            raise ValidationError(
                {
                    "status": (
                        f"Invalid status transition from "
                        f"{WorkAssignment.Status(assignment.status).label} to "
                        f"{WorkAssignment.Status(new_status).label}."
                    )
                }
            )
        return Response(
            {
                "success": True,
                "message": (
                    f"Assignment moved to {WorkAssignment.Status(new_status).label}."
                ),
                "assignment": WorkAssignmentSerializer(
                    assignment, context=self.get_serializer_context()
                ).data,
            }
        )
