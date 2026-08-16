"""Assign-work availability tests.

Covers the order detail ``assignment_summary`` (the backend-authoritative
"can I still assign work" signal the frontend uses to show/hide the Assign Work
button) plus the terminal-order guard that rejects new assignments on
COLLECTED / CANCELLED orders. Availability depends only on ``assigned_quantity``
totals vs ordered quantity - completed quantity is never used.
"""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.orders.models import OrderStatus
from apps.tailors.tests.helpers import (
    assign_payload,
    create_assignment,
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_staff,
    work_assignments_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _detail(client, order, staff):
    response = client.get(f"/api/v1/orders/{order.id}/", **_auth(staff))
    assert response.status_code == 200
    return response.json()["assignment_summary"]


def _assign(client, staff, tailor, order, item, quantity):
    response = client.post(
        work_assignments_url(),
        assign_payload(tailor, order, item, assigned_quantity=quantity),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    return response


@pytest.mark.parametrize(
    ("assigned", "expected_assigned", "expected_remaining", "expected_can_assign"),
    [
        ([], 0, 3, True),
        ([1], 1, 2, True),
        ([2], 2, 1, True),
        ([3], 3, 0, False),
    ],
)
def test_three_shirts_availability_progress(
    client, staff, assigned, expected_assigned, expected_remaining, expected_can_assign
):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    for quantity in assigned:
        _assign(client, staff, tailor, order, item, quantity)

    summary =     _detail(client, order, staff)
    assert summary["total_quantity"] == 3
    assert summary["assigned_quantity"] == expected_assigned
    assert summary["remaining_unassigned"] == expected_remaining
    assert summary["can_assign_work"] is expected_can_assign


def test_multiple_tailors_assignments_sum_together(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    _assign(client, staff, tailor_a, order, item, 1)
    _assign(client, staff, tailor_b, order, item, 2)

    summary =     _detail(client, order, staff)
    assert summary["total_quantity"] == 3
    assert summary["assigned_quantity"] == 3
    assert summary["remaining_unassigned"] == 0
    assert summary["can_assign_work"] is False


def test_remaining_ignores_completed_quantity(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    # 2 assigned and fully completed: availability still reflects the unassigned
    # piece because completed work does not free an unassigned piece.
    create_assignment(tailor, item, assigned_quantity=2, completed_quantity=2)

    summary =     _detail(client, order, staff)
    assert summary["assigned_quantity"] == 2
    assert summary["remaining_unassigned"] == 1
    assert summary["can_assign_work"] is True


def test_mixed_garments_partial_assignment_keeps_assign_work(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2, "PANT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    create_piece_rate(garment_type="PANT")

    _assign(client, staff, tailor, order, get_order_item(order, "SHIRT"), 2)

    summary =     _detail(client, order, staff)
    assert summary["total_quantity"] == 5
    assert summary["assigned_quantity"] == 2
    assert summary["remaining_unassigned"] == 3
    assert summary["can_assign_work"] is True


def test_mixed_garments_all_assigned_disables_assign_work(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2, "PANT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    create_piece_rate(garment_type="PANT")

    _assign(client, staff, tailor, order, get_order_item(order, "SHIRT"), 2)
    _assign(client, staff, tailor, order, get_order_item(order, "PANT"), 3)

    summary =     _detail(client, order, staff)
    assert summary["total_quantity"] == 5
    assert summary["assigned_quantity"] == 5
    assert summary["remaining_unassigned"] == 0
    assert summary["can_assign_work"] is False


@pytest.mark.parametrize(
    "status", [OrderStatus.COLLECTED, OrderStatus.CANCELLED]
)
def test_terminal_order_cannot_receive_new_assignment(client, staff, status):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    order.status = status
    order.save(update_fields=["status"])
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    response = client.post(
        work_assignments_url(),
        assign_payload(tailor, order, item, assigned_quantity=1),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "validation_error"
    detail = response.json()["error"]["details"]["order"]
    assert OrderStatus(status).label in detail


@pytest.mark.parametrize(
    "status", [OrderStatus.COLLECTED, OrderStatus.CANCELLED]
)
def test_terminal_order_never_assignable_even_with_remaining(client, staff, status):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    order.status = status
    order.save(update_fields=["status"])

    summary =     _detail(client, order, staff)
    assert summary["total_quantity"] == 3
    assert summary["assigned_quantity"] == 0
    assert summary["remaining_unassigned"] == 3
    assert summary["can_assign_work"] is False
