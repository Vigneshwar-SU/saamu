"""Shared helpers for tailors, piece rate and work assignment tests."""

from apps.customers.tests.helpers import (  # noqa: F401
    create_customer,
    make_owner,
    make_staff,
)
from apps.tailors.models import PieceRate, Tailor, WorkAssignment

PASSWORD = "test-password-123"


def tailors_url():
    return "/api/v1/tailors/"


def tailor_url(tailor_id):
    return f"/api/v1/tailors/{tailor_id}/"


def tailor_archive_url(tailor_id):
    return f"/api/v1/tailors/{tailor_id}/archive/"


def tailor_restore_url(tailor_id):
    return f"/api/v1/tailors/{tailor_id}/restore/"


def tailor_earnings_url(tailor_id):
    return f"/api/v1/tailors/{tailor_id}/earnings/"


def piece_rates_url():
    return "/api/v1/piece-rates/"


def piece_rate_url(rate_id):
    return f"/api/v1/piece-rates/{rate_id}/"


def work_assignments_url():
    return "/api/v1/work-assignments/"


def work_assignment_url(assignment_id):
    return f"/api/v1/work-assignments/{assignment_id}/"


def work_assignment_status_url(assignment_id):
    return f"/api/v1/work-assignments/{assignment_id}/status/"


def tailor_earnings_summary_url():
    return "/api/v1/tailor-earnings/summary/"


def valid_tailor_payload(**extra):
    payload = {
        "name": "Arun Stitcher",
        "mobile_number": "9123456780",
        "notes": "Master tailor.",
    }
    payload.update(extra)
    return payload


def valid_piece_rate_payload(**extra):
    payload = {"garment_type": "SHIRT", "rate_per_piece": "150.00"}
    payload.update(extra)
    return payload


def create_tailor(full_name="Arun Stitcher", is_active=True, **kwargs):
    defaults = {"full_name": full_name, "is_active": is_active}
    defaults.update(kwargs)
    return Tailor.objects.create(**defaults)


def create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00", is_active=True):
    return PieceRate.objects.create(
        garment_type=garment_type, rate_per_piece=rate_per_piece, is_active=is_active
    )


def create_measurement(customer, garment_type="SHIRT"):
    from apps.orders.tests.helpers import create_measurement as _cm

    return _cm(customer, garment_type=garment_type)


def create_order(customer, items=None, **extra):
    """Create an order with one or more OrderItems via the API serializer."""
    from types import SimpleNamespace

    from apps.orders.serializers import OrderCreateSerializer
    from apps.orders.tests.helpers import valid_order_payload

    payload = valid_order_payload(customer, items=items, **extra)
    serializer = OrderCreateSerializer(
        data=payload,
        context={
            "request": SimpleNamespace(user=SimpleNamespace(is_authenticated=False))
        },
    )
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def create_order_with_items(customer, garment_quantities):
    """Create an order where each garment has a specific quantity.

    ``garment_quantities`` is a dict like ``{"SHIRT": 5, "PANT": 3}``.
    """
    items = []
    for garment, quantity in garment_quantities.items():
        measurement = create_measurement(customer, garment_type=garment)
        items.append(
            {
                "garment_type": garment,
                "quantity": quantity,
                "unit_price": "100.00",
                "measurement_id": measurement.id,
            }
        )
    return create_order(customer, items=items)


def get_order_item(order, garment_type):
    return order.items.filter(garment_type=garment_type).first()


def create_assignment(
    tailor,
    order_item,
    assigned_quantity=None,
    completed_quantity=0,
    status=WorkAssignment.Status.ASSIGNED,
    rate_per_piece_snapshot="150.00",
    **kwargs,
):
    if assigned_quantity is None:
        assigned_quantity = order_item.quantity
    assignment = WorkAssignment.objects.create(
        tailor=tailor,
        order_item=order_item,
        assigned_quantity=assigned_quantity,
        completed_quantity=completed_quantity,
        status=status,
        rate_per_piece_snapshot=rate_per_piece_snapshot,
        **kwargs,
    )
    return assignment


def assign_payload(tailor, order, order_item, assigned_quantity=None, **extra):
    payload = {
        "tailor": tailor.id,
        "order": order.id,
        "order_item": order_item.id,
    }
    if assigned_quantity is not None:
        payload["assigned_quantity"] = assigned_quantity
    payload.update(extra)
    return payload
