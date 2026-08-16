"""Move-to-ready workflow tests.

Covers the STITCHING -> READY work-completion checkpoint:

- A. Status transition: the plain status endpoint only allows STITCHING ->
  READY once every ordered piece is reported complete (backend-authoritative,
  so a direct/manual request cannot bypass the checkpoint); other transitions
  are unchanged.
- B. Completion calculation: remaining-to-complete is computed from
  ``completed_quantity`` totals only -- an assignment status of COMPLETED
  without a completed quantity never counts, across multiple tailors and mixed
  garments.
- C. Work-progress endpoint: read-only authoritative progress with a per-item
  breakdown, readable by OWNER and STAFF.
- D. Side effects: moving to READY never auto-completes assignments.
- E. RBAC: moving to ready stays STAFF-only.

Expected error contract is the project standard
``{"success": false, "error": {"code": "validation_error", ...}}``.
"""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.orders.models import Order, OrderStatus, OrderStatusHistory
from apps.orders.tests.helpers import (
    order_status_url,
    order_work_progress_url,
)
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

READY_READINESS_MESSAGE = (
    "All assigned work must be completed before the order can be marked ready."
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


def _progress(client, user, order_id):
    return client.get(order_work_progress_url(order_id), **_auth(user))


def _set_status(order, status):
    order.status = status
    order.save(update_fields=["status"])


def _make_order(garments, assigned=None, completed=None):
    """Create a STITCHING order with fully assigned, partly completed work.

    ``garments`` maps garment code to quantity; ``assigned`` / ``completed``
    default to the full quantity per garment. A ``None`` in ``completed`` keeps
    that garment's completion at zero so tests can model partial progress.
    """
    customer = create_customer()
    order = create_order_with_items(customer, garments)
    tailor = create_tailor()
    for garment, quantity in garments.items():
        create_piece_rate(garment_type=garment)
        item = get_order_item(order, garment)
        assigned_qty = assigned if assigned is not None else quantity
        completed_qty = completed if completed is not None else 0
        create_assignment(
            tailor,
            item,
            assigned_quantity=assigned_qty,
            completed_quantity=completed_qty,
        )
    _set_status(order, OrderStatus.STITCHING)
    return order


# ---------------------------------------------------------------------------
# A. Status transition (STITCHING -> READY gate on the plain status endpoint)
# ---------------------------------------------------------------------------


def test_stitching_all_work_completed_moves_to_ready(client, staff):
    order = _make_order({"SHIRT": 3}, completed=3)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["success"] is True
    assert body["order"]["status"] == "READY"
    history = OrderStatusHistory.objects.filter(
        order_id=order.id, to_status=OrderStatus.READY
    )
    assert history.count() == 1
    assert history.first().from_status == OrderStatus.STITCHING


def test_stitching_partially_completed_ready_rejected(client, staff):
    order = _make_order({"SHIRT": 3}, completed=1)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert READY_READINESS_MESSAGE in body["error"]["message"]
    assert Order.objects.get(pk=order.id).status == OrderStatus.STITCHING
    assert (
        OrderStatusHistory.objects.filter(
            order_id=order.id, to_status=OrderStatus.READY
        ).count()
        == 0
    )


def test_stitching_zero_completed_ready_rejected(client, staff):
    order = _make_order({"SHIRT": 3}, completed=0)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert READY_READINESS_MESSAGE in response.json()["error"]["message"]
    assert Order.objects.get(pk=order.id).status == OrderStatus.STITCHING


def test_assigned_status_without_completion_ready_rejected(client, staff):
    """An assignment marked ASSIGNED -- even fully assigned -- is not complete."""
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=2, completed_quantity=0)
    _set_status(order, OrderStatus.STITCHING)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 400
    assert READY_READINESS_MESSAGE in response.json()["error"]["message"]


def test_in_progress_status_without_completion_ready_rejected(client, staff):
    """An assignment marked IN_PROGRESS is not complete."""
    from apps.tailors.models import WorkAssignment

    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(
        tailor,
        item,
        assigned_quantity=2,
        completed_quantity=0,
        status=WorkAssignment.Status.IN_PROGRESS,
    )
    _set_status(order, OrderStatus.STITCHING)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 400
    assert READY_READINESS_MESSAGE in response.json()["error"]["message"]


def test_completed_status_with_zero_quantity_ready_rejected(client, staff):
    """A COMPLETED badge without reported pieces never counts as done."""
    from apps.tailors.models import WorkAssignment

    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(
        tailor,
        item,
        assigned_quantity=2,
        completed_quantity=0,
        status=WorkAssignment.Status.COMPLETED,
    )
    _set_status(order, OrderStatus.STITCHING)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 400
    assert READY_READINESS_MESSAGE in response.json()["error"]["message"]


def test_multiple_assignments_aggregate_toward_completion(client, staff):
    """Two tailors splitting a garment both count toward completion."""
    from apps.tailors.models import WorkAssignment

    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor_a, item, assigned_quantity=2, completed_quantity=2)
    create_assignment(tailor_b, item, assigned_quantity=1, completed_quantity=0)
    _set_status(order, OrderStatus.STITCHING)

    rejected = _transition(client, staff, order.id, "READY")
    assert rejected.status_code == 400
    assert READY_READINESS_MESSAGE in rejected.json()["error"]["message"]

    remaining = WorkAssignment.objects.get(order_item=item, tailor=tailor_b)
    remaining.completed_quantity = 1
    remaining.status = WorkAssignment.Status.COMPLETED
    remaining.save(update_fields=["completed_quantity", "status"])

    accepted = _transition(client, staff, order.id, "READY")
    assert accepted.status_code == 200, accepted.json()
    assert accepted.json()["order"]["status"] == "READY"


def test_mixed_garments_need_all_completed_moves_to_ready(client, staff):
    from apps.tailors.models import WorkAssignment

    order = _make_order({"SHIRT": 2, "PANT": 3}, completed=0)
    shirt = get_order_item(order, "SHIRT")
    pant = get_order_item(order, "PANT")

    rejected = _transition(client, staff, order.id, "READY")
    assert rejected.status_code == 400
    assert READY_READINESS_MESSAGE in rejected.json()["error"]["message"]

    WorkAssignment.objects.filter(order_item=pant).update(completed_quantity=3)
    still_incomplete = _transition(client, staff, order.id, "READY")
    assert still_incomplete.status_code == 400
    assert READY_READINESS_MESSAGE in still_incomplete.json()["error"]["message"]

    WorkAssignment.objects.filter(order_item=shirt).update(completed_quantity=2)
    accepted = _transition(client, staff, order.id, "READY")
    assert accepted.status_code == 200, accepted.json()
    assert accepted.json()["order"]["status"] == "READY"


def test_non_ready_transitions_unchanged(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    create_assignment(tailor, item, assigned_quantity=1)
    _set_status(order, OrderStatus.CUTTING)

    response = _transition(client, staff, order.id, "STITCHING")
    assert response.status_code == 200, response.json()
    assert response.json()["order"]["status"] == "STITCHING"


def test_ready_to_collected_unchanged(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    _set_status(order, OrderStatus.READY)

    response = _transition(client, staff, order.id, "COLLECTED")
    assert response.status_code == 200, response.json()
    assert response.json()["order"]["status"] == "COLLECTED"


# ---------------------------------------------------------------------------
# B. Work-progress calculation
# ---------------------------------------------------------------------------


def test_work_progress_reports_remaining(client, staff):
    order = _make_order({"SHIRT": 3, "PANT": 2}, completed=0)

    response = _progress(client, staff, order.id)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_required"] == 5
    assert data["total_assigned"] == 5
    assert data["total_completed"] == 0
    assert data["remaining_to_complete"] == 5
    assert data["all_work_completed"] is False
    assert len(data["items"]) == 2
    by_garment = {item["garment_type"]: item for item in data["items"]}
    assert by_garment["SHIRT"]["quantity"] == 3
    assert by_garment["SHIRT"]["remaining"] == 3
    assert by_garment["PANT"]["remaining"] == 2


def test_work_progress_partial_completion(client, staff):
    from apps.tailors.models import WorkAssignment

    order = _make_order({"SHIRT": 3, "PANT": 2}, completed=0)
    shirt = get_order_item(order, "SHIRT")
    pant = get_order_item(order, "PANT")
    WorkAssignment.objects.filter(order_item=shirt).update(completed_quantity=3)
    WorkAssignment.objects.filter(order_item=pant).update(completed_quantity=1)

    data = _progress(client, staff, order.id).json()["data"]
    assert data["total_completed"] == 4
    assert data["remaining_to_complete"] == 1
    assert data["all_work_completed"] is False
    by_garment = {item["garment_type"]: item for item in data["items"]}
    assert by_garment["SHIRT"]["completed_quantity"] == 3
    assert by_garment["SHIRT"]["remaining"] == 0
    assert by_garment["PANT"]["completed_quantity"] == 1
    assert by_garment["PANT"]["remaining"] == 1


def test_work_progress_completed_all_work(client, staff):
    order = _make_order({"SHIRT": 3}, completed=3)

    data = _progress(client, staff, order.id).json()["data"]
    assert data["total_completed"] == 3
    assert data["remaining_to_complete"] == 0
    assert data["all_work_completed"] is True


def test_work_progress_is_read_only(client, staff):
    order = _make_order({"SHIRT": 3}, completed=1)
    before = _progress(client, staff, order.id).json()["data"]

    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)(
            order_work_progress_url(order.id), **_auth(staff)
        )
        assert response.status_code == 405

    after = _progress(client, staff, order.id).json()["data"]
    assert after == before


# ---------------------------------------------------------------------------
# C. Side effects: moving to ready never auto-completes assignments
# ---------------------------------------------------------------------------


def test_ready_transition_does_not_auto_complete_assignments(client, staff):
    from apps.tailors.models import WorkAssignment

    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    assignment = create_assignment(
        tailor,
        item,
        assigned_quantity=2,
        completed_quantity=2,
        status=WorkAssignment.Status.IN_PROGRESS,
    )
    _set_status(order, OrderStatus.STITCHING)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 200, response.json()

    refreshed = WorkAssignment.objects.get(pk=assignment.pk)
    assert refreshed.completed_quantity == 2
    assert refreshed.status == WorkAssignment.Status.IN_PROGRESS


# ---------------------------------------------------------------------------
# D. RBAC
# ---------------------------------------------------------------------------


def test_owner_cannot_move_to_ready(client, owner, staff):
    order = _make_order({"SHIRT": 1}, completed=1)

    response = _transition(client, owner, order.id, "READY")
    assert response.status_code == 403


def test_owner_can_read_work_progress(client, owner):
    order = _make_order({"SHIRT": 1}, completed=0)

    response = _progress(client, owner, order.id)
    assert response.status_code == 200
    assert response.json()["data"]["all_work_completed"] is False


def test_staff_can_move_to_ready(client, staff):
    order = _make_order({"SHIRT": 1}, completed=1)

    response = _transition(client, staff, order.id, "READY")
    assert response.status_code == 200, response.json()
    assert response.json()["order"]["status"] == "READY"
