"""Measurement permission tests: OWNER view-only, STAFF create/modify."""

import pytest

from apps.customers.models import Measurement
from apps.customers.tests.helpers import (
    create_customer,
    make_owner,
    make_staff,
    measurement_detail_url,
    measurements_url,
    valid_shirt_payload,
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
    return create_customer()


def _auth(user):
    from apps.authentication.tests.helpers import auth_header

    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def test_anonymous_cannot_list_measurements(client, customer):
    assert client.get(measurements_url(customer.id)).status_code == 401


def test_anonymous_cannot_create_measurement(client, customer):
    response = client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_anonymous_cannot_view_measurement(client, customer):
    measurement = Measurement.objects.create(
        customer=customer, garment_type="SHIRT", version=1
    )
    assert client.get(measurement_detail_url(measurement.id)).status_code == 401


def test_anonymous_cannot_update_measurement(client, customer):
    measurement = Measurement.objects.create(
        customer=customer, garment_type="SHIRT", version=1
    )
    response = client.patch(
        measurement_detail_url(measurement.id),
        {"notes": "Hacked"},
        content_type="application/json",
    )
    assert response.status_code == 401


def test_owner_can_view_measurement_list(client, owner, customer):
    Measurement.objects.create(customer=customer, garment_type="SHIRT", version=1)
    response = client.get(measurements_url(customer.id), **_auth(owner))
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_owner_can_view_measurement_detail(client, owner, customer):
    measurement = Measurement.objects.create(
        customer=customer, garment_type="SHIRT", version=1
    )
    response = client.get(measurement_detail_url(measurement.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["id"] == measurement.id


def test_owner_cannot_create_measurement(client, owner, customer):
    response = client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_owner_cannot_update_measurement(client, owner, customer):
    measurement = Measurement.objects.create(
        customer=customer, garment_type="SHIRT", version=1
    )
    response = client.patch(
        measurement_detail_url(measurement.id),
        {"notes": "Changed"},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_staff_can_create_measurement(client, staff, customer):
    response = client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["version"] == 1
    assert response.json()["is_current"] is True


def test_staff_can_update_measurement_by_creating_new_version(client, staff, customer):
    created = client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    ).json()

    payload = valid_shirt_payload()
    payload["chest_circumference"] = 42.0
    response = client.patch(
        measurement_detail_url(created["id"]),
        payload,
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["version"] == 2
    assert response.json()["is_current"] is True
    assert response.json()["chest_circumference"] == 42.0
