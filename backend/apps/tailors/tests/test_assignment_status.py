"""Work assignment status lifecycle tests: ASSIGNED -> IN_PROGRESS -> COMPLETED."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.tailors.models import WorkAssignment
from apps.tailors.tests.helpers import (
    create_assignment,
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_staff,
    work_assignment_status_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


@pytest.fixture
def assignment(staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 5})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")
    item = get_order_item(order, "SHIRT")
    return create_assignment(tailor, item, assigned_quantity=5)


def _transition(client, staff, assignment_id, payload):
    return client.post(
        work_assignment_status_url(assignment_id),
        payload,
        content_type="application/json",
        **_auth(staff),
    )


def test_assigned_to_in_progress(client, staff, assignment):
    response = _transition(client, staff, assignment.id, {"status": "IN_PROGRESS"})
    assert response.status_code == 200
    assignment.refresh_from_db()
    assert assignment.status == WorkAssignment.Status.IN_PROGRESS
    assert assignment.started_at is not None


def test_in_progress_to_completed_full_quantity(client, staff, assignment):
    _transition(client, staff, assignment.id, {"status": "IN_PROGRESS"})
    response = _transition(client, staff, assignment.id, {"status": "COMPLETED"})
    assert response.status_code == 200
    assignment.refresh_from_db()
    assert assignment.status == WorkAssignment.Status.COMPLETED
    assert assignment.completed_quantity == 5
    assert assignment.completed_at is not None


def test_in_progress_to_completed_partial_quantity(client, staff, assignment):
    _transition(client, staff, assignment.id, {"status": "IN_PROGRESS"})
    response = _transition(
        client, staff, assignment.id, {"status": "COMPLETED", "completed_quantity": 3}
    )
    assert response.status_code == 200
    assignment.refresh_from_db()
    assert assignment.status == WorkAssignment.Status.COMPLETED
    assert assignment.completed_quantity == 3


def test_completed_quantity_cannot_exceed_assigned(client, staff, assignment):
    _transition(client, staff, assignment.id, {"status": "IN_PROGRESS"})
    response = _transition(
        client, staff, assignment.id, {"status": "COMPLETED", "completed_quantity": 6}
    )
    assert response.status_code == 400
    assert (
        "assigned quantity" in response.json()["error"]["details"]["completed_quantity"]
    )


def test_skip_transition_rejected(client, staff, assignment):
    response = _transition(client, staff, assignment.id, {"status": "COMPLETED"})
    assert response.status_code == 400
    assert "transition" in response.json()["error"]["message"]


def test_invalid_status_rejected(client, staff, assignment):
    response = _transition(client, staff, assignment.id, {"status": "BOGUS"})
    assert response.status_code == 400


def test_completed_cannot_be_reopened(client, staff, assignment):
    _transition(client, staff, assignment.id, {"status": "IN_PROGRESS"})
    _transition(client, staff, assignment.id, {"status": "COMPLETED"})
    response = _transition(client, staff, assignment.id, {"status": "IN_PROGRESS"})
    assert response.status_code == 400
    assignment.refresh_from_db()
    assert assignment.status == WorkAssignment.Status.COMPLETED


def test_owner_cannot_transition_status(client, assignment):
    from apps.customers.tests.helpers import make_owner

    owner = make_owner()
    response = _transition(client, owner, assignment.id, {"status": "IN_PROGRESS"})
    assert response.status_code == 403


def test_earned_amount_reflects_completed_quantity(client, staff, assignment):
    _transition(client, staff, assignment.id, {"status": "IN_PROGRESS"})
    _transition(
        client, staff, assignment.id, {"status": "COMPLETED", "completed_quantity": 3}
    )
    response = client.get(f"/api/v1/work-assignments/{assignment.id}/", **_auth(staff))
    assert response.json()["earned_amount"] == 450.0
