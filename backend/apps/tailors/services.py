"""Work assignment business logic for Saamu Tailors.

Centralizes the authoritative creation of work assignments so the standalone
assignment endpoint (``POST /work-assignments/``) and the combined
"assign remaining work + move to stitching" operation share one path. All
safety rules live here:

- Assignments require an active tailor and an active piece rate for the
  garment; the rate is snapshotted at assignment time so later rate edits
  never rewrite history.
- The order row is locked before the item row so every assignment writer
  acquires locks in the same order (order -> item). Concurrent assignments
  serialize on those rows and can never over-allocate a garment.
- ``assigned_quantity`` is checked against the item's *remaining* quantity
  (ordered quantity minus the sum of existing assigned quantities) under the
  row lock. Completed quantity is deliberately ignored here.
- Terminal orders (COLLECTED / CANCELLED) can never receive new work.
"""

from django.db import models, transaction
from rest_framework.exceptions import ValidationError

from apps.orders.models import TERMINAL_STATUSES, Order, OrderItem

from .models import PieceRate, WorkAssignment


def create_work_assignment(*, tailor, order_item, assigned_quantity, created_by=None):
    """Create one work assignment, enforcing every assignment safety rule.

    Returns the created ``WorkAssignment``. Raises ``ValidationError`` (in the
    project's standard field-error shape) when the tailor is inactive, the
    piece rate is missing, the order is terminal, or the quantity would exceed
    the item's remaining unassigned quantity.

    Lock ordering is order row first, then item row. This mirrors the order in
    which the combined "move to stitching" service locks, so concurrent
    assignment writers never deadlock.
    """
    if not tailor.is_active:
        raise ValidationError(
            {"tailor": "Assignments can only be created for active tailors."}
        )
    if not isinstance(assigned_quantity, int) or assigned_quantity < 1:
        raise ValidationError(
            {"assigned_quantity": "Assigned quantity must be a positive whole number."}
        )

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
        # Lock the order row first so every writer shares one lock ordering and
        # the terminal-status check is stable for the whole operation.
        order = Order.objects.select_for_update().get(pk=order_item.order_id)
        if order.status in TERMINAL_STATUSES:
            raise ValidationError(
                {
                    "order": (
                        f"Work cannot be assigned to this order because it "
                        f"is {order.get_status_display()}."
                    )
                }
            )
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
        return WorkAssignment.objects.create(
            tailor=tailor,
            order_item=locked_item,
            assigned_quantity=assigned_quantity,
            completed_quantity=0,
            rate_per_piece_snapshot=rate.rate_per_piece,
            created_by=created_by,
        )
