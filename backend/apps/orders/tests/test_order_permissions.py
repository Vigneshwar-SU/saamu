"""Order RBAC tests: anonymous rejection, owner read-only access and
staff-only mutations."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.orders.tests.helpers import (
    create_measurement,
    make_owner,
    make_staff,
    order_detail_url,
    order_item_payload,
    order_list_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return make_owner()


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def customer():
    from apps.customers.tests.helpers import create_customer

    return create_customer()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _create(client, user, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    return client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [order_item_payload("SHIRT", measurement_id=measurement.id)],
        },
        content_type="application/json",
        **_auth(user),
    )


def test_anonymous_cannot_list_orders(client):
    response = client.get(order_list_url())
    assert response.status_code == 401


def test_anonymous_cannot_create_order(client, customer):
    response = client.post(order_list_url(), {}, content_type="application/json")
    assert response.status_code == 401


def test_owner_can_list_orders(client, owner, customer):
    _create(client, make_staff(), customer)
    response = client.get(order_list_url(), **_auth(owner))
    assert response.status_code == 200


def test_owner_can_retrieve_order(client, owner, staff, customer):
    order = _create(client, staff, customer).json()
    response = client.get(order_detail_url(order["id"]), **_auth(owner))
    assert response.status_code == 200


def test_owner_cannot_create_order(client, owner, customer):
    response = _create(client, owner, customer)
    assert response.status_code == 403


def test_owner_cannot_transition_status(client, owner, staff, customer):
    order = _create(client, staff, customer).json()
    response = client.post(
        f"/api/v1/orders/{order['id']}/status/",
        {"status": "CUTTING"},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_staff_can_create_order(client, staff, customer):
    response = _create(client, staff, customer)
    assert response.status_code == 201
