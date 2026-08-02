"""Tailors RBAC tests: anonymous rejection, owner read-only access and
staff-only mutations."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.tailors.tests.helpers import (
    assign_payload,
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_owner,
    make_staff,
    piece_rates_url,
    tailor_archive_url,
    tailor_url,
    tailors_url,
    valid_tailor_payload,
    work_assignments_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return make_owner()


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def test_anonymous_cannot_list_tailors(client):
    response = client.get(tailors_url())
    assert response.status_code == 401


def test_anonymous_cannot_create_tailor(client):
    response = client.post(
        tailors_url(), valid_tailor_payload(), content_type="application/json"
    )
    assert response.status_code == 401


def test_owner_can_list_tailors(client, owner):
    create_tailor()
    response = client.get(tailors_url(), **_auth(owner))
    assert response.status_code == 200


def test_owner_can_retrieve_tailor(client, owner):
    tailor = create_tailor()
    response = client.get(tailor_url(tailor.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["name"] == "Arun Stitcher"


def test_owner_can_view_earnings(client, owner):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    item = get_order_item(order, "SHIRT")
    response = client.post(
        work_assignments_url(),
        assign_payload(tailor, order, item, assigned_quantity=2),
        content_type="application/json",
        **_auth(make_staff("staff_create")),
    )
    assert response.status_code == 201

    earnings_response = client.get(
        f"/api/v1/tailors/{tailor.id}/earnings/", **_auth(owner)
    )
    assert earnings_response.status_code == 200
    assert earnings_response.json()["summary"]["total_completed_quantity"] == 0


def test_owner_cannot_create_tailor(client, owner):
    response = client.post(
        tailors_url(),
        valid_tailor_payload(),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_owner_cannot_archive_tailor(client, owner):
    tailor = create_tailor()
    response = client.post(tailor_archive_url(tailor.id), **_auth(owner))
    assert response.status_code == 403


def test_owner_cannot_create_piece_rate(client, owner):
    response = client.post(
        piece_rates_url(),
        {"garment_type": "SHIRT", "rate_per_piece": "150.00"},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_owner_cannot_create_assignment(client, owner):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT")
    response = client.post(
        work_assignments_url(),
        assign_payload(
            tailor, order, get_order_item(order, "SHIRT"), assigned_quantity=1
        ),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_staff_can_create_tailor(client, staff):
    response = client.post(
        tailors_url(),
        valid_tailor_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
