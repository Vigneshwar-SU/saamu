"""Move-to-stitching workflow tests.

Covers the CUTTING -> STITCHING assignment checkpoint:

- A. Status transition: the plain status endpoint only allows CUTTING ->
  STITCHING once every piece is assigned; other transitions are unchanged.
- B. Assignment quantity: remaining-unassigned is computed from assigned
  quantities only, across multiple tailors and mixed garments.
- C. Combined operation: ``POST /orders/{id}/move-to-stitching/`` assigns
  remaining work and transitions atomically (or reports what remains).
- D. Concurrency: simultaneous assignment writers cannot over-assign.
- E. RBAC: moving to stitching stays STAFF-only.

Expected error contract is the project standard
``{"success": false, "error": {"code": "validation_error", ...}}``.
"""

import threading

import pytest
from rest_framework.exceptions import ValidationError

from apps.customers.tests.helpers import auth_header
from apps.orders.models import Order, OrderStatus, OrderStatusHistory
from apps.orders.tests.helpers import (
    order_detail_url,
    order_move_to_stitching_url,
    order_status_url,
)
from apps.tailors.models import WorkAssignment
from apps.tailors.services import create_work_assignment
from apps.tailors.tests.helpers import (
    create_assignment,
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_owner,
    make_staff,
)

pytestmark = pytest.mark.django_db

STITCHING_READINESS_MESSAGE = (
    "All work must be assigned before the order can move to stitching."
)


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _transition(client, user, order_id, status):
    return client.post(
        order_status_url(order_id),
        {"status": status},
        content_type="application/json",
        **_auth(user),
    )


def _move(client, user, order_id, payload=None):
    return client.post(
        order_move_to_stitching_url(order_id),
        data=payload if payload is not None else {},
        content_type="application/json",
        **_auth(user),
    )


def _set_status(order, status):
    order.status = status
    order.save(update_fields=["status"])


def _assignment_payload(order, item, tailor, quantity):
    return {
        "tailor": tailor.id,
        "order_item": item.id,
        "assigned_quantity": quantity,
    }


# ---------------------------------------------------------------------------
# A. Status transition (CUTTING -> STITCHING gate on the plain status endpoint)
# ---------------------------------------------------------------------------


def test_cutting_fully_assigned_moves_to_stitching(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=3)
    _set_status(order, OrderStatus.CUTTING)

    response = _transition(client, staff, order.id, "STITCHING")
    assert response.status_code == 200, response.json()
    assert response.json()["order"]["status"] == "STITCHING"
    history = OrderStatusHistory.objects.filter(
        order_id=order.id, to_status=OrderStatus.STITCHING
    )
    assert history.count() == 1
    assert history.first().from_status == OrderStatus.CUTTING


def test_cutting_partially_assigned_stitching_rejected(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=1)
    _set_status(order, OrderStatus.CUTTING)

    response = _transition(client, staff, order.id, "STITCHING")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert STITCHING_READINESS_MESSAGE in body["error"]["message"]
    assert Order.objects.get(pk=order.id).status == OrderStatus.CUTTING
    assert (
        OrderStatusHistory.objects.filter(
            order_id=order.id, to_status=OrderStatus.STITCHING
        ).count()
        == 0
    )


def test_cutting_zero_assigned_stitching_rejected(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    _set_status(order, OrderStatus.CUTTING)

    response = _transition(client, staff, order.id, "STITCHING")
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert STITCHING_READINESS_MESSAGE in body["error"]["message"]
    assert Order.objects.get(pk=order.id).status == OrderStatus.CUTTING


def test_ready_transition_unchanged(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=1, completed_quantity=1)
    _set_status(order, OrderStatus.STITCHING)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 200, response.json()
    assert response.json()["order"]["status"] == "READY"


def test_collected_terminal_unchanged(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    _set_status(order, OrderStatus.COLLECTED)

    response = _transition(client, staff, order.id, "STITCHING")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert Order.objects.get(pk=order.id).status == OrderStatus.COLLECTED


def test_cancelled_terminal_unchanged(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    _set_status(order, OrderStatus.CANCELLED)

    response = _transition(client, staff, order.id, "CUTTING")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert Order.objects.get(pk=order.id).status == OrderStatus.CANCELLED


# ---------------------------------------------------------------------------
# B. Assignment quantity calculation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("assigned", "expected_assigned", "expected_remaining"),
    [
        (1, 1, 2),
        (2, 2, 1),
        (3, 3, 0),
    ],
)
def test_three_shirts_remaining(
    client, staff, assigned, expected_assigned, expected_remaining
):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=assigned)

    summary = client.get(order_detail_url(order.id), **_auth(staff)).json()[
        "assignment_summary"
    ]
    assert summary["total_quantity"] == 3
    assert summary["assigned_quantity"] == expected_assigned
    assert summary["remaining_unassigned"] == expected_remaining


def test_multiple_tailors_summed(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor_a, item, assigned_quantity=1)
    create_assignment(tailor_b, item, assigned_quantity=2)

    summary = client.get(order_detail_url(order.id), **_auth(staff)).json()[
        "assignment_summary"
    ]
    assert summary["assigned_quantity"] == 3
    assert summary["remaining_unassigned"] == 0


def test_mixed_garments_calculated(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2, "PANT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    create_piece_rate(garment_type="PANT")
    create_assignment(tailor, get_order_item(order, "SHIRT"), assigned_quantity=2)
    create_assignment(tailor, get_order_item(order, "PANT"), assigned_quantity=3)

    summary = client.get(order_detail_url(order.id), **_auth(staff)).json()[
        "assignment_summary"
    ]
    assert summary["total_quantity"] == 5
    assert summary["assigned_quantity"] == 5
    assert summary["remaining_unassigned"] == 0


def test_remaining_ignores_completed_quantity(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=2, completed_quantity=2)

    summary = client.get(order_detail_url(order.id), **_auth(staff)).json()[
        "assignment_summary"
    ]
    assert summary["assigned_quantity"] == 2
    assert summary["remaining_unassigned"] == 1


def test_over_assignment_rejected(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    _set_status(order, OrderStatus.CUTTING)

    response = _move(
        client,
        staff,
        order.id,
        {"assignments": [_assignment_payload(order, item, tailor, 4)]},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert "remain" in response.json()["error"]["message"]
    assert WorkAssignment.objects.filter(order_item=item).count() == 0
    assert Order.objects.get(pk=order.id).status == OrderStatus.CUTTING


@pytest.mark.parametrize("quantity", [0, -1])
def test_invalid_quantity_rejected(client, staff, quantity):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    response = _move(
        client,
        staff,
        order.id,
        {"assignments": [_assignment_payload(order, item, tailor, quantity)]},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert WorkAssignment.objects.filter(order_item=item).count() == 0


# ---------------------------------------------------------------------------
# C. Combined operation (assign + move to stitching)
# ---------------------------------------------------------------------------


def test_combined_assign_remaining_and_transition_atomically(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    _set_status(order, OrderStatus.CUTTING)

    first = _move(
        client,
        staff,
        order.id,
        {"assignments": [_assignment_payload(order, item, tailor, 1)]},
    )
    assert first.status_code == 200, first.json()
    body = first.json()
    assert body["transitioned"] is False
    assert body["message"] == "2 pieces are still unassigned."
    assert body["assignment_summary"]["remaining_unassigned"] == 2
    assert body["order"]["status"] == "CUTTING"
    assert Order.objects.get(pk=order.id).status == OrderStatus.CUTTING
    assert WorkAssignment.objects.filter(order_item=item).count() == 1

    second = _move(
        client,
        staff,
        order.id,
        {"assignments": [_assignment_payload(order, item, tailor, 2)]},
    )
    assert second.status_code == 200, second.json()
    body = second.json()
    assert body["transitioned"] is True
    assert body["message"] == "Work assigned successfully. Order moved to stitching."
    assert body["assignment_summary"]["remaining_unassigned"] == 0
    assert body["order"]["status"] == "STITCHING"
    assert Order.objects.get(pk=order.id).status == OrderStatus.STITCHING
    assert WorkAssignment.objects.filter(order_item=item).count() == 2

    history = OrderStatusHistory.objects.filter(order_id=order.id).order_by("id")
    assert list(history.values_list("from_status", "to_status")) == [
        (None, "NEW"),
        ("CUTTING", "STITCHING"),
    ]


def test_combined_incomplete_keeps_order_in_cutting(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    _set_status(order, OrderStatus.CUTTING)

    response = _move(
        client,
        staff,
        order.id,
        {"assignments": [_assignment_payload(order, item, tailor, 1)]},
    )
    assert response.status_code == 200
    assert response.json()["transitioned"] is False
    assert Order.objects.get(pk=order.id).status == OrderStatus.CUTTING
    assert (
        OrderStatusHistory.objects.filter(
            order_id=order.id, to_status=OrderStatus.STITCHING
        ).count()
        == 0
    )


def test_combined_validation_failure_rolls_back_all_assignments(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    _set_status(order, OrderStatus.CUTTING)

    payload = {
        "assignments": [
            _assignment_payload(order, item, tailor, 2),
            _assignment_payload(order, item, tailor, 2),
        ]
    }
    response = _move(client, staff, order.id, payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert WorkAssignment.objects.filter(order_item=item).count() == 0
    assert Order.objects.get(pk=order.id).status == OrderStatus.CUTTING


def test_combined_rejects_item_from_another_order_no_partial_state(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    other_order = create_order_with_items(customer, {"PANT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    create_piece_rate(garment_type="PANT")
    item = get_order_item(order, "SHIRT")
    _set_status(order, OrderStatus.CUTTING)

    response = _move(
        client,
        staff,
        order.id,
        {
            "assignments": [
                _assignment_payload(
                    other_order, get_order_item(other_order, "PANT"), tailor, 1
                )
            ]
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert WorkAssignment.objects.count() == 0
    assert Order.objects.get(pk=order.id).status == OrderStatus.CUTTING


def test_combined_on_non_cutting_rejected_no_assignments(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    _set_status(order, OrderStatus.STITCHING)

    response = _move(
        client,
        staff,
        order.id,
        {"assignments": [_assignment_payload(order, item, tailor, 1)]},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert WorkAssignment.objects.filter(order_item=item).count() == 0
    assert Order.objects.get(pk=order.id).status == OrderStatus.STITCHING


def test_combined_fully_assigned_without_assignments_transitions(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=3)
    _set_status(order, OrderStatus.CUTTING)

    response = _move(client, staff, order.id)
    assert response.status_code == 200, response.json()
    assert response.json()["transitioned"] is True
    assert response.json()["order"]["status"] == "STITCHING"
    assert WorkAssignment.objects.filter(order_item=item).count() == 1


def test_combined_final_assignment_auto_transitions(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=2)
    _set_status(order, OrderStatus.CUTTING)

    response = _move(
        client,
        staff,
        order.id,
        {"assignments": [_assignment_payload(order, item, tailor, 1)]},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["transitioned"] is True
    assert response.json()["order"]["status"] == "STITCHING"
    assert response.json()["assignment_summary"]["remaining_unassigned"] == 0


def test_combined_multiple_tailors_and_garments_transitions(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2, "PANT": 3})
    babu = create_tailor("Babu")
    ravi = create_tailor("Ravi")
    create_piece_rate(garment_type="SHIRT")
    create_piece_rate(garment_type="PANT")
    shirt_item = get_order_item(order, "SHIRT")
    pant_item = get_order_item(order, "PANT")
    _set_status(order, OrderStatus.CUTTING)

    response = _move(
        client,
        staff,
        order.id,
        {
            "assignments": [
                _assignment_payload(order, shirt_item, babu, 2),
                _assignment_payload(order, pant_item, ravi, 3),
            ]
        },
    )
    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["transitioned"] is True
    assert body["order"]["status"] == "STITCHING"
    assert body["assignment_summary"]["total_quantity"] == 5
    assert body["assignment_summary"]["assigned_quantity"] == 5
    assert body["assignment_summary"]["remaining_unassigned"] == 0
    assert WorkAssignment.objects.filter(order_item__order_id=order.id).count() == 2


# ---------------------------------------------------------------------------
# D. Concurrency / over-assignment
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_concurrent_assignments_cannot_exceed_required_quantity(staff):
    """Two writers assigning 2 each to a 3-piece item: one wins, one is
    rejected, and the total assigned never exceeds 3."""
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    outcomes = []
    lock = threading.Lock()

    def worker(quantity):
        from django.db import connection

        connection.close()
        try:
            try:
                create_work_assignment(
                    tailor=tailor,
                    order_item=item,
                    assigned_quantity=quantity,
                    created_by=staff,
                )
                result = "ok"
            except ValidationError:
                result = "rejected"
        except Exception as exc:  # pragma: no cover - defensive
            result = f"error:{exc}"
        finally:
            connection.close()
        with lock:
            outcomes.append(result)

    threads = [
        threading.Thread(target=worker, args=(2,)),
        threading.Thread(target=worker, args=(2,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["ok", "rejected"]
    total = sum(
        assignment.assigned_quantity
        for assignment in WorkAssignment.objects.filter(order_item=item)
    )
    assert total == 2


# ---------------------------------------------------------------------------
# E. RBAC
# ---------------------------------------------------------------------------


def test_owner_cannot_move_to_stitching(client, owner, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=1)
    _set_status(order, OrderStatus.CUTTING)

    response = _move(client, owner, order.id)
    assert response.status_code == 403

    status_response = _transition(client, owner, order.id, "STITCHING")
    assert status_response.status_code == 403


def test_owner_can_read_order_detail(client, owner, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})

    response = client.get(order_detail_url(order.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["id"] == order.id


def test_staff_can_move_to_stitching(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=1)
    _set_status(order, OrderStatus.CUTTING)

    response = _move(client, staff, order.id)
    assert response.status_code == 200, response.json()
    assert response.json()["order"]["status"] == "STITCHING"
