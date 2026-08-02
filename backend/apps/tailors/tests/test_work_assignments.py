"""Work assignment creation, quantity validation and consumption tests."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.tailors.models import WorkAssignment
from apps.tailors.tests.helpers import (
    assign_payload,
    create_assignment,
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_staff,
    work_assignment_url,
    work_assignments_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def test_staff_can_create_assignment(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 5})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")

    response = client.post(
        work_assignments_url(),
        assign_payload(
            tailor, order, get_order_item(order, "SHIRT"), assigned_quantity=2
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["assigned_quantity"] == 2
    assert data["status"] == WorkAssignment.Status.ASSIGNED
    assert data["rate_per_piece_snapshot"] == 150.0
    assert data["tailor"]["id"] == tailor.id
    assert data["order_item"]["order_number"] == order.order_number
    assert data["order_item"]["customer_name"] == customer.full_name
    assert data["earned_amount"] == 0.0


def test_assignment_to_inactive_tailor_rejected(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 5})
    tailor = create_tailor(is_active=False)
    create_piece_rate(garment_type="SHIRT")

    response = client.post(
        work_assignments_url(),
        assign_payload(
            tailor, order, get_order_item(order, "SHIRT"), assigned_quantity=2
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "active" in response.json()["error"]["details"]["tailor"][0]


def test_invalid_order_item_rejected(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 5})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")

    response = client.post(
        work_assignments_url(),
        {
            "tailor": tailor.id,
            "order": order.id,
            "order_item": 999999,
            "assigned_quantity": 2,
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "order_item" in response.json()["error"]["details"]


def test_order_item_mismatch_rejected(client, staff):
    customer = create_customer()
    order_a = create_order_with_items(customer, {"SHIRT": 2})
    order_b = create_order_with_items(customer, {"PANT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    create_piece_rate(garment_type="PANT")

    item_a = get_order_item(order_a, "SHIRT")
    response = client.post(
        work_assignments_url(),
        assign_payload(tailor, order_b, item_a, assigned_quantity=1),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "does not belong" in response.json()["error"]["details"]["order_item"][0]


def test_assignment_quantity_must_be_positive(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 5})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")

    response = client.post(
        work_assignments_url(),
        assign_payload(
            tailor, order, get_order_item(order, "SHIRT"), assigned_quantity=0
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_assignment_quantity_above_remaining_rejected(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    first = client.post(
        work_assignments_url(),
        assign_payload(tailor, order, item, assigned_quantity=2),
        content_type="application/json",
        **_auth(staff),
    )
    assert first.status_code == 201

    response = client.post(
        work_assignments_url(),
        assign_payload(tailor, order, item, assigned_quantity=2),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "remain" in response.json()["error"]["details"]["assigned_quantity"]


def test_multiple_assignments_consume_remaining(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 5})
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    r1 = client.post(
        work_assignments_url(),
        assign_payload(tailor_a, order, item, assigned_quantity=2),
        content_type="application/json",
        **_auth(staff),
    )
    r2 = client.post(
        work_assignments_url(),
        assign_payload(tailor_b, order, item, assigned_quantity=1),
        content_type="application/json",
        **_auth(staff),
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    response = client.post(
        work_assignments_url(),
        assign_payload(tailor_a, order, item, assigned_quantity=3),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "remain" in response.json()["error"]["details"]["assigned_quantity"]


def test_full_quantity_can_be_assigned(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 4})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")

    response = client.post(
        work_assignments_url(),
        assign_payload(
            tailor, order, get_order_item(order, "SHIRT"), assigned_quantity=4
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201


def test_remaining_quantity_exposed_on_order_items(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 5})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    order_response = client.get(f"/api/v1/orders/{order.id}/", **_auth(staff))
    item_data = next(i for i in order_response.json()["items"] if i["id"] == item.id)
    assert item_data["remaining_quantity"] == 5
    assert item_data["assigned_quantity"] == 0

    client.post(
        work_assignments_url(),
        assign_payload(tailor, order, item, assigned_quantity=2),
        content_type="application/json",
        **_auth(staff),
    )

    order_response = client.get(f"/api/v1/orders/{order.id}/", **_auth(staff))
    item_data = next(i for i in order_response.json()["items"] if i["id"] == item.id)
    assert item_data["assigned_quantity"] == 2
    assert item_data["remaining_quantity"] == 3


def test_list_filters_by_tailor(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 4})
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    create_assignment(tailor_a, item, assigned_quantity=2)
    create_assignment(tailor_b, item, assigned_quantity=2)

    response = client.get(
        work_assignments_url(), {"tailor": tailor_a.id}, **_auth(staff)
    )
    assert response.status_code == 200
    ids = [a["id"] for a in response.json()["results"]]
    assert len(ids) == 1


def test_list_filters_by_status(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 4})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")

    create_assignment(tailor, item, assigned_quantity=2)
    create_assignment(
        tailor, item, assigned_quantity=2, status=WorkAssignment.Status.IN_PROGRESS
    )

    response = client.get(
        work_assignments_url(), {"status": "IN_PROGRESS"}, **_auth(staff)
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["status"] == "IN_PROGRESS"


def test_list_filters_invalid_status_rejected(client, staff):
    response = client.get(work_assignments_url(), {"status": "BOGUS"}, **_auth(staff))
    assert response.status_code == 400


def test_assignment_can_be_retrieved(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    assignment = create_assignment(tailor, item, assigned_quantity=2)

    response = client.get(work_assignment_url(assignment.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["id"] == assignment.id


def test_historical_assignments_visible_after_tailor_archived(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    assignment = create_assignment(tailor, item, assigned_quantity=2)

    client.post(f"/api/v1/tailors/{tailor.id}/archive/", **_auth(staff))

    response = client.get(work_assignment_url(assignment.id), **_auth(staff))
    assert response.status_code == 200
