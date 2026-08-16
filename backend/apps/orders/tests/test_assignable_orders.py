"""Assignable-orders filter tests (``?assignable=true``).

The orders list powers the Assign Work picker, so it must only ever surface
orders that can genuinely receive tailoring work: unassigned pieces must remain
and the order must not be terminal. Filtering happens in SQL before pagination,
so a page never mixes in finished orders that the UI would have to hide later.

The rule mirrors the authoritative per-instance ``order_assignment_state``
calculation: availability depends only on ``assigned_quantity`` totals vs the
ordered quantity, never on ``completed_quantity``.
"""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.orders.models import OrderStatus
from apps.orders.tests.helpers import order_list_url
from apps.tailors.tests.helpers import (
    assign_payload,
    create_customer,
    create_order,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_owner,
    make_staff,
    work_assignments_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _assignable_ids(client, user, query=""):
    response = client.get(f"{order_list_url()}?assignable=true{query}", **_auth(user))
    assert response.status_code == 200
    return response.json()


def _create_assignments(client, staff, entries):
    for tailor, order, item, quantity in entries:
        response = client.post(
            work_assignments_url(),
            assign_payload(tailor, order, item, assigned_quantity=quantity),
            content_type="application/json",
            **_auth(staff),
        )
        assert response.status_code == 201, response.content


def _order_ids(body):
    return {entry["id"] for entry in body["results"]}


def test_completely_unassigned_order_included(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    create_piece_rate(garment_type="SHIRT")

    body = _assignable_ids(client, staff)
    assert body["count"] == 1
    assert _order_ids(body) == {order.id}


def test_fully_assigned_order_excluded(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    _create_assignments(client, staff, [(tailor, order, item, 3)])

    body = _assignable_ids(client, staff)
    assert body["count"] == 0
    assert order.id not in _order_ids(body)


def test_partially_assigned_order_included(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    _create_assignments(client, staff, [(tailor, order, item, 1)])

    body = _assignable_ids(client, staff)
    assert body["count"] == 1
    assert order.id in _order_ids(body)


def test_partially_assigned_item_keeps_remaining(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    _create_assignments(client, staff, [(tailor, order, item, 1)])

    detail = client.get(f"/api/v1/orders/{order.id}/", **_auth(staff)).json()
    item_data = next(i for i in detail["items"] if i["id"] == item.id)
    assert item_data["assigned_quantity"] == 1
    assert item_data["remaining_quantity"] == 2
    assert detail["assignment_summary"]["can_assign_work"] is True


@pytest.mark.parametrize("status", [OrderStatus.COLLECTED, OrderStatus.CANCELLED])
def test_terminal_order_excluded_even_with_remaining(client, staff, status):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    order.status = status
    order.save(update_fields=["status"])
    create_piece_rate(garment_type="SHIRT")

    body = _assignable_ids(client, staff)
    assert body["count"] == 0
    assert order.id not in _order_ids(body)


def test_ready_order_with_unassigned_work_still_included(client, staff):
    # READY is not terminal; if a READY order somehow still has unassigned
    # pieces the backend-authoritative rule keeps it assignable.
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    order.status = OrderStatus.READY
    order.save(update_fields=["status"])

    body = _assignable_ids(client, staff)
    assert body["count"] == 1
    assert order.id in _order_ids(body)


def test_multiple_garments_partial_assignment_stays_assignable(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2, "PANT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    create_piece_rate(garment_type="PANT")
    _create_assignments(
        client, staff, [(tailor, order, get_order_item(order, "SHIRT"), 2)]
    )

    body = _assignable_ids(client, staff)
    assert body["count"] == 1
    assert order.id in _order_ids(body)


def test_multiple_garments_all_assigned_excluded(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2, "PANT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    create_piece_rate(garment_type="PANT")
    _create_assignments(
        client,
        staff,
        [
            (tailor, order, get_order_item(order, "SHIRT"), 2),
            (tailor, order, get_order_item(order, "PANT"), 3),
        ],
    )

    body = _assignable_ids(client, staff)
    assert body["count"] == 0
    assert order.id not in _order_ids(body)


def test_final_assignment_removes_order(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    _create_assignments(client, staff, [(tailor, order, item, 2)])
    assert order.id in _order_ids(_assignable_ids(client, staff))

    _create_assignments(client, staff, [(tailor, order, item, 1)])
    body = _assignable_ids(client, staff)
    assert body["count"] == 0
    assert order.id not in _order_ids(body)


def test_filtering_happens_before_pagination(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")

    fully_assigned = []
    assignable = []
    for _ in range(4):
        order = create_order(customer, items=["SHIRT"])
        _create_assignments(
            client, staff, [(tailor, order, get_order_item(order, "SHIRT"), 1)]
        )
        fully_assigned.append(order.id)
    for _ in range(4):
        assignable.append(create_order(customer, items=["SHIRT"]).id)

    body = _assignable_ids(client, staff)
    assert body["count"] == 4
    assert len(body["results"]) == 4
    assert _order_ids(body) == set(assignable)
    assert not set(fully_assigned) & _order_ids(body)


def test_owner_can_read_assignable_orders(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    create_piece_rate(garment_type="SHIRT")

    owner = make_owner()
    body = _assignable_ids(client, owner)
    assert body["count"] == 1
    assert order.id in _order_ids(body)


def test_invalid_assignable_value_rejected(client, staff):
    response = client.get(order_list_url() + "?assignable=maybe", **_auth(staff))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_assignable_false_keeps_existing_list_behavior(client, staff):
    customer = create_customer()
    assignable_order = create_order(customer, items=["SHIRT"])
    terminal_order = create_order(customer, items=["SHIRT"])
    terminal_order.status = OrderStatus.CANCELLED
    terminal_order.save(update_fields=["status"])

    response = client.get(order_list_url() + "?assignable=false", **_auth(staff))
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert _order_ids(body) == {assignable_order.id, terminal_order.id}


def test_over_assignment_still_rejected_after_filtering(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    _create_assignments(client, staff, [(tailor, order, item, 2)])
    assert order.id in _order_ids(_assignable_ids(client, staff))

    response = client.post(
        work_assignments_url(),
        assign_payload(tailor, order, item, assigned_quantity=2),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "remain" in response.json()["error"]["details"]["assigned_quantity"]

    body = _assignable_ids(client, staff)
    assert order.id in _order_ids(body)
