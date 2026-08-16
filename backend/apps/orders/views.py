"""Order views for the Saamu Tailors API.

Permission model (backend authoritative):
- Read (list/detail) -> OWNER or STAFF.
- Mutations (create, safe PATCH, status transitions) -> STAFF only.
- Orders are never physically deleted (no DELETE method).

Status changes are only possible through the dedicated
``POST /api/v1/orders/{id}/status/`` action, which validates the lifecycle.
"""

from datetime import date

from django.db import models, transaction
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.common.pagination import SaamuPageNumberPagination
from apps.orders.models import (
    ALLOWED_TRANSITIONS,
    Order,
    OrderStatus,
    OrderStatusHistory,
)
from apps.orders.serializers import (
    MoveToStitchingSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
    OrderUpdateSerializer,
)
from apps.orders.services import (
    assign_and_move_to_stitching,
    order_work_progress,
    require_all_work_completed_for_ready,
    require_fully_assigned_for_stitching,
)

ORDER_MUTATION_ACTIONS = {
    "create",
    "partial_update",
    "change_status",
    "create_invoice",
    "move_to_stitching",
}


class OrderViewSet(viewsets.ModelViewSet):
    """Orders: list/search/filter/detail for OWNER+STAFF; create/update/status
    for STAFF only. No physical deletion."""

    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = OrderSerializer
    pagination_class = SaamuPageNumberPagination

    def get_permissions(self):
        if self.action in ORDER_MUTATION_ACTIONS:
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "partial_update":
            return OrderUpdateSerializer
        return OrderSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["include_payment_summary"] = self.action == "retrieve"
        context["include_assignment_summary"] = self.action == "retrieve"
        return context

    def get_queryset(self):
        qs = (
            Order.objects.select_related("customer")
            .prefetch_related(
                "items",
                "items__measurement",
                "items__work_assignments",
                "status_history",
                "status_history__changed_by",
            )
            .all()
        )
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        """Search + status + date filtering for the list endpoint.

        Search matches order number, customer full name or customer mobile.
        ``?status=NEW`` filters by exact status. ``?date_from`` / ``?date_to``
        filter by order date (inclusive, YYYY-MM-DD).
        """
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                models.Q(order_number__icontains=search)
                | models.Q(customer__full_name__icontains=search)
                | models.Q(customer__mobile_number__icontains=search)
            )

        status_filter = (self.request.query_params.get("status") or "").strip()
        if status_filter:
            if status_filter not in OrderStatus.values:
                raise ValidationError({"status": "Invalid order status filter."})
            qs = qs.filter(status=status_filter)

        date_from = (self.request.query_params.get("date_from") or "").strip()
        if date_from:
            qs = qs.filter(order_date__gte=date_from)
        date_to = (self.request.query_params.get("date_to") or "").strip()
        if date_to:
            qs = qs.filter(order_date__lte=date_to)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            OrderSerializer(order, context=self.get_serializer_context()).data,
            status=http_status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            OrderSerializer(order, context=self.get_serializer_context()).data
        )

    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, pk=None):
        """Transition an order to a new status (STAFF only).

        Body: ``{"status": "CUTTING"}``. Backend validates the lifecycle.
        COLLECTED records ``collected_at``. COLLECTED and CANCELLED are
        terminal. A history row is appended for every transition.

        CUTTING -> STITCHING additionally requires every piece to be assigned
        to a tailor: while any work remains unassigned the transition is
        rejected, so a direct/manual request cannot bypass the assignment
        checkpoint. STITCHING -> READY additionally requires every ordered
        piece to be reported complete: while any work remains incomplete the
        transition is rejected, so a direct/manual request cannot bypass the
        work-completion checkpoint. The order row is locked while the
        transition is validated and written so concurrent
        assignment/progress/transition requests serialize.
        """
        order = self.get_object()

        if order.status in (OrderStatus.COLLECTED, OrderStatus.CANCELLED):
            raise ValidationError(
                {
                    "status": (
                        f"This order is already {order.get_status_display()}. "
                        "Terminal orders cannot change status."
                    )
                }
            )

        serializer = OrderStatusUpdateSerializer(
            data=request.data, context={"order": order}
        )
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        with transaction.atomic():
            locked_order = Order.objects.select_for_update().get(pk=order.pk)

            if locked_order.status in (OrderStatus.COLLECTED, OrderStatus.CANCELLED):
                raise ValidationError(
                    {
                        "status": (
                            f"This order is already "
                            f"{locked_order.get_status_display()}. "
                            "Terminal orders cannot change status."
                        )
                    }
                )
            if new_status not in ALLOWED_TRANSITIONS.get(locked_order.status, set()):
                raise ValidationError(
                    {
                        "status": (
                            f"Invalid status transition from "
                            f"{locked_order.get_status_display()} to "
                            f"{OrderStatus(new_status).label}."
                        )
                    }
                )
            if (
                new_status == OrderStatus.STITCHING
                and locked_order.status == OrderStatus.CUTTING
            ):
                require_fully_assigned_for_stitching(locked_order)
            if (
                new_status == OrderStatus.READY
                and locked_order.status == OrderStatus.STITCHING
            ):
                require_all_work_completed_for_ready(locked_order)

            previous_status = locked_order.status
            locked_order.status = new_status
            if new_status == OrderStatus.COLLECTED:
                locked_order.collected_at = timezone.now()
            locked_order.save(
                update_fields=[
                    "status",
                    "collected_at",
                    "updated_at",
                ]
            )
            OrderStatusHistory.objects.create(
                order=locked_order,
                from_status=previous_status,
                to_status=new_status,
                changed_by=request.user,
            )

        return Response(
            {
                "success": True,
                "message": (
                    f"Order {locked_order.order_number} moved to "
                    f"{OrderStatus(new_status).label}."
                ),
                "order": OrderSerializer(
                    locked_order, context=self.get_serializer_context()
                ).data,
            },
            status=http_status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="work-progress")
    def work_progress(self, request, pk=None):
        """Authoritative work-completion progress for an order (OWNER+STAFF).

        Read-only. Reports how many of the ordered pieces are assigned and how
        many are reported complete, so the client can decide whether "Move to
        Ready" is available and show exactly what remains when it is not.
        """
        order = self.get_object()
        return Response(
            {"success": True, "data": order_work_progress(order)},
            status=http_status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="move-to-stitching")
    def move_to_stitching(self, request, pk=None):
        """Assign remaining work and move a CUTTING order to STITCHING (STAFF).

        Body (optional): ``{"assignments": [{"tailor", "order_item",
        "assigned_quantity"}, ...]}``.

        Runs as one transaction: assignments are validated and saved under row
        locks (never over-assigning), then assignment completeness is
        recomputed from authoritative database state. If every piece is now
        assigned the order transitions to STITCHING; otherwise it stays in
        CUTTING and the response reports how many pieces remain unassigned so
        the client can continue assigning. Either outcome is returned
        atomically -- a partial success is impossible.
        """
        order = self.get_object()
        serializer = MoveToStitchingSerializer(
            data=request.data, context={"order": order}
        )
        serializer.is_valid(raise_exception=True)
        assignments = serializer.validated_data.get("assignments") or []

        result = assign_and_move_to_stitching(
            order=order,
            user=request.user,
            assignments=assignments,
        )
        moved_order = self.get_queryset().get(pk=order.pk)
        state = result["state"]

        if result["transitioned"]:
            message = "Work assigned successfully. Order moved to stitching."
        else:
            remaining = state["remaining_unassigned"]
            message = (
                f"{remaining} piece{' is' if remaining == 1 else 's are'} "
                "still unassigned."
            )

        return Response(
            {
                "success": True,
                "message": message,
                "transitioned": result["transitioned"],
                "assignment_summary": state,
                "order": OrderSerializer(
                    moved_order, context=self.get_serializer_context()
                ).data,
            },
            status=http_status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="invoice")
    def create_invoice(self, request, pk=None):
        """Create an invoice for this order (STAFF).

        Convenience endpoint that delegates to the billing layer, so it shares
        the one-invoice-per-order rule, the immutable item snapshots and the
        server-generated invoice number with ``POST /invoices/``. The billing
        import is deliberately local to keep the apps decoupled.
        """
        from apps.billing.serializers import InvoiceSerializer
        from apps.billing.services import create_invoice_for_order

        order = self.get_object()
        invoice = create_invoice_for_order(
            order=order,
            invoice_date=request.data.get("invoice_date"),
            notes=request.data.get("notes", ""),
            created_by=request.user,
        )
        return Response(
            {
                "success": True,
                "message": f"Invoice {invoice.invoice_number} created.",
                "invoice": InvoiceSerializer(
                    invoice, context=self.get_serializer_context()
                ).data,
            },
            status=http_status.HTTP_201_CREATED,
        )
