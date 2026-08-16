"""Order business logic for the Saamu Tailors API.

Centralizes the assignment-readiness calculation (used by the order serializer,
the status transition endpoint and the combined "move to stitching" endpoint),
the work-completion calculation that gates "move to ready", and the combined
operation that assigns remaining work and then advances a CUTTING order to
STITCHING.

Two rules are enforced here:

- An order may only leave CUTTING once every piece has been assigned to a
  tailor. ``remaining_unassigned`` is computed from ``assigned_quantity``
  totals only -- completed quantity is deliberately never used, because a piece
  is only "handled" once it has been handed to a tailor.
- An order may only leave STITCHING once every ordered piece has been reported
  complete. ``remaining_to_complete`` is computed from ``completed_quantity``
  totals only -- an assignment being marked COMPLETED without a completed
  quantity never counts.
"""

from django.db import models, transaction
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from apps.tailors.models import WorkAssignment
from apps.tailors.services import create_work_assignment

from .models import TERMINAL_STATUSES, Order, OrderItem, OrderStatus, OrderStatusHistory

STITCHING_READINESS_MESSAGE = (
    "All work must be assigned before the order can move to stitching."
)

READY_READINESS_MESSAGE = (
    "All assigned work must be completed before the order can be marked ready."
)


def order_assignment_state(order):
    """Authoritative assignment state for one order.

    Returns a dict with ``total_quantity`` (sum of ordered pieces),
    ``assigned_quantity`` (sum of assigned quantities across every item) and
    ``remaining_unassigned``. ``can_assign_work`` is True only while unassigned
    pieces remain AND the order is not terminal.
    """
    total_quantity = 0
    assigned_quantity = 0
    for item in order.items.all():
        total_quantity += item.quantity
        for assignment in item.work_assignments.all():
            assigned_quantity += assignment.assigned_quantity
    remaining_unassigned = max(total_quantity - assigned_quantity, 0)
    return {
        "total_quantity": total_quantity,
        "assigned_quantity": assigned_quantity,
        "remaining_unassigned": remaining_unassigned,
        "can_assign_work": remaining_unassigned > 0 and not order.is_terminal,
    }


def filter_assignable_orders(qs):
    """DB-level filter keeping only orders that can still receive work.

    Mirrors the per-instance rule in :func:`order_assignment_state`: an order is
    assignable while unassigned pieces remain (ordered quantity minus the sum of
    ``assigned_quantity`` across every work assignment) AND the order is not in
    a terminal state (COLLECTED / CANCELLED). Completed quantity is never used,
    matching the assignment-authority definition.

    The two totals are computed as scalar subqueries on the outer ``Order``
    query, so the filter runs in SQL *before* pagination: the returned page
    never contains orders that would later have to be hidden client-side, and
    the ``count`` reflects only genuinely assignable orders.
    """
    ordered = (
        OrderItem.objects.filter(order=models.OuterRef("pk"))
        .values("order")
        .annotate(total=models.Sum("quantity"))
        .values("total")
    )
    assigned = (
        WorkAssignment.objects.filter(order_item__order=models.OuterRef("pk"))
        .values("order_item__order")
        .annotate(total=models.Sum("assigned_quantity"))
        .values("total")
    )
    return (
        qs.exclude(status__in=TERMINAL_STATUSES)
        .annotate(
            remaining_unassigned_work=(
                Coalesce(models.Subquery(ordered), models.Value(0))
                - Coalesce(models.Subquery(assigned), models.Value(0))
            )
        )
        .filter(remaining_unassigned_work__gt=0)
    )


def require_fully_assigned_for_stitching(order):
    """Raise ``ValidationError`` when a CUTTING order is not fully assigned.

    Used by the status transition endpoint so a direct, manual request moving
    a CUTTING order to STITCHING is rejected while work remains unassigned.
    """
    state = order_assignment_state(order)
    if state["remaining_unassigned"] > 0:
        raise ValidationError({"status": STITCHING_READINESS_MESSAGE})
    return state


def order_work_progress(order):
    """Authoritative work-completion progress for one order.

    Returns a dict with ``total_required`` (sum of ordered pieces),
    ``total_assigned`` and ``total_completed`` (sums of assigned/completed
    quantities across every assignment) plus ``remaining_to_complete`` and
    ``all_work_completed``. ``all_work_completed`` is True only when the
    reported completed quantity covers every ordered piece; an assignment
    status of COMPLETED without a completed quantity never counts. A per-item
    breakdown is included so the client can show exactly what remains.
    """
    total_required = 0
    total_assigned = 0
    total_completed = 0
    items = []
    for item in order.items.all():
        item_assigned = 0
        item_completed = 0
        for assignment in item.work_assignments.all():
            item_assigned += assignment.assigned_quantity
            item_completed += assignment.completed_quantity
        total_required += item.quantity
        total_assigned += item_assigned
        total_completed += item_completed
        items.append(
            {
                "order_item_id": item.id,
                "garment_type": item.garment_type,
                "garment_label": item.get_garment_type_display(),
                "quantity": item.quantity,
                "assigned_quantity": item_assigned,
                "completed_quantity": item_completed,
                "remaining": max(item.quantity - item_completed, 0),
            }
        )
    remaining_to_complete = max(total_required - total_completed, 0)
    return {
        "total_required": total_required,
        "total_assigned": total_assigned,
        "total_completed": total_completed,
        "remaining_to_complete": remaining_to_complete,
        "all_work_completed": total_completed >= total_required,
        "items": items,
    }


def require_all_work_completed_for_ready(order):
    """Raise ``ValidationError`` when a STITCHING order has incomplete work.

    Used by the status transition endpoint so a direct, manual request moving
    a STITCHING order to READY is rejected while any ordered piece remains
    unreported complete.
    """
    progress = order_work_progress(order)
    if not progress["all_work_completed"]:
        raise ValidationError({"status": READY_READINESS_MESSAGE})
    return progress


def assign_and_move_to_stitching(*, order, user, assignments):
    """Assign remaining work and advance a CUTTING order to STITCHING.

    Transaction-safe combined operation:

    - Locks the order row so concurrent assignments/transitions serialize.
    - Validates the order is currently CUTTING and not terminal.
    - Creates every requested assignment through the shared assignment service
      (which locks order -> item and prevents over-assignment).
    - Recomputes assignment completeness from authoritative database state.
    - If every piece is assigned, transitions the order to STITCHING, appends a
      status history row and commits everything atomically. If any step fails,
      the whole operation rolls back and the order stays in CUTTING.

    ``assignments`` is a list of ``{"tailor", "order_item", "assigned_quantity"}``
    dicts (or objects with the same attributes).

    Returns ``{"transitioned": bool, "order": Order, "state": dict}``.
    """
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order.pk)
        if locked_order.status != OrderStatus.CUTTING:
            raise ValidationError(
                {
                    "status": (
                        "Only orders in CUTTING can move to stitching. "
                        f"This order is {locked_order.get_status_display()}."
                    )
                }
            )
        if locked_order.is_terminal:
            raise ValidationError(
                {"status": "Terminal orders cannot move to stitching."}
            )

        for entry in assignments:
            order_item = entry["order_item"]
            if order_item.order_id != locked_order.pk:
                raise ValidationError(
                    {
                        "assignments": {
                            "order_item": (
                                "The selected order item does not belong to this order."
                            )
                        }
                    }
                )
            create_work_assignment(
                tailor=entry["tailor"],
                order_item=order_item,
                assigned_quantity=entry["assigned_quantity"],
                created_by=user,
            )

        state = order_assignment_state(locked_order)
        if state["remaining_unassigned"] > 0:
            return {
                "transitioned": False,
                "order": locked_order,
                "state": state,
            }

        previous_status = locked_order.status
        locked_order.status = OrderStatus.STITCHING
        locked_order.save(update_fields=["status", "updated_at"])
        OrderStatusHistory.objects.create(
            order=locked_order,
            from_status=previous_status,
            to_status=OrderStatus.STITCHING,
            changed_by=user,
        )
        state["can_assign_work"] = False
        return {
            "transitioned": True,
            "order": locked_order,
            "state": state,
        }
