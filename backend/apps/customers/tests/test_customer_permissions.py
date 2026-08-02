"""Permission tests: anonymous, OWNER view-only, STAFF management."""

import pytest

from apps.authentication.tests.helpers import auth_header
from apps.customers.tests.helpers import (
    create_customer,
    customer_archive_url,
    customer_detail_url,
    customer_list_url,
    customer_restore_url,
    make_owner,
    make_staff,
    valid_customer_payload,
)

pytestmark = pytest.mark.django_db


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


@pytest.fixture
def owner():
    return make_owner()


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def customer():
    return create_customer()


def test_anonymous_cannot_list_customers(client):
    assert client.get(customer_list_url()).status_code == 401


def test_anonymous_cannot_view_customer_detail(client, customer):
    assert client.get(customer_detail_url(customer.id)).status_code == 401


def test_anonymous_cannot_create_customer(client):
    response = client.post(
        customer_list_url(), valid_customer_payload(), content_type="application/json"
    )
    assert response.status_code == 401


def test_anonymous_cannot_update_customer(client, customer):
    response = client.patch(
        customer_detail_url(customer.id),
        {"full_name": "Hacked"},
        content_type="application/json",
    )
    assert response.status_code == 401


def test_anonymous_cannot_archive_customer(client, customer):
    response = client.post(customer_archive_url(customer.id))
    assert response.status_code == 401


def test_owner_can_list_customers(client, owner, customer):
    response = client.get(customer_list_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_owner_can_view_customer_detail(client, owner, customer):
    response = client.get(customer_detail_url(customer.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["id"] == customer.id


def test_owner_cannot_create_customer(client, owner):
    response = client.post(
        customer_list_url(),
        valid_customer_payload(),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_owner_cannot_update_customer(client, owner, customer):
    response = client.patch(
        customer_detail_url(customer.id),
        {"full_name": "Changed"},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_owner_cannot_archive_customer(client, owner, customer):
    response = client.post(customer_archive_url(customer.id), **_auth(owner))
    assert response.status_code == 403


def test_owner_cannot_restore_customer(client, owner, customer):
    response = client.post(customer_restore_url(customer.id), **_auth(owner))
    assert response.status_code == 403


def test_staff_can_create_customer(client, staff):
    response = client.post(
        customer_list_url(),
        valid_customer_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["full_name"] == "Ravi Kumar"


def test_staff_can_update_customer(client, staff, customer):
    response = client.patch(
        customer_detail_url(customer.id),
        {"full_name": "Ravi Kumar Updated"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Ravi Kumar Updated"


def test_staff_can_archive_customer(client, staff, customer):
    response = client.post(customer_archive_url(customer.id), **_auth(staff))
    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.is_active is False


def test_staff_can_restore_customer(client, staff, customer):
    customer.is_active = False
    customer.save(update_fields=["is_active"])
    response = client.post(customer_restore_url(customer.id), **_auth(staff))
    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.is_active is True
