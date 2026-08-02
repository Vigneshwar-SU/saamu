"""Measurement relationship tests: correct-customer ownership and isolation."""

import pytest

from apps.customers.models import Measurement
from apps.customers.tests.helpers import (
    create_customer,
    make_staff,
    measurement_detail_url,
    measurements_url,
    valid_shirt_payload,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(staff):
    from apps.authentication.tests.helpers import auth_header

    return {"HTTP_AUTHORIZATION": auth_header(staff)["HTTP_AUTHORIZATION"]}


def test_measurement_belongs_to_the_correct_customer(client, staff):
    customer_a = create_customer(full_name="A", mobile_number="9000000001")
    customer_b = create_customer(full_name="B", mobile_number="9000000002")

    response = client.post(
        measurements_url(customer_a.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["customer"] == customer_a.id

    stored = Measurement.objects.get(pk=response.json()["id"])
    assert stored.customer_id == customer_a.id


def test_measurements_are_isolated_between_customers(client, staff):
    customer_a = create_customer(full_name="A", mobile_number="9000000001")
    customer_b = create_customer(full_name="B", mobile_number="9000000002")

    client.post(
        measurements_url(customer_a.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )

    list_a = client.get(measurements_url(customer_a.id), **_auth(staff))
    list_b = client.get(measurements_url(customer_b.id), **_auth(staff))
    assert len(list_a.json()) == 1
    assert list_b.json() == []


def test_creating_measurement_for_missing_customer_returns_404(client, staff):
    response = client.post(
        measurements_url(99999),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_listing_measurements_for_missing_customer_returns_404(client, staff):
    response = client.get(measurements_url(99999), **_auth(staff))
    assert response.status_code == 404


def test_measurement_detail_for_missing_returns_404(client, staff):
    response = client.get(measurement_detail_url(99999), **_auth(staff))
    assert response.status_code == 404


def test_measurement_update_does_not_move_to_another_customer(client, staff):
    customer_a = create_customer(full_name="A", mobile_number="9000000001")
    customer_b = create_customer(full_name="B", mobile_number="9000000002")

    created = client.post(
        measurements_url(customer_a.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    ).json()

    payload = valid_shirt_payload()
    payload["chest_circumference"] = 41.0
    response = client.patch(
        measurement_detail_url(created["id"]),
        payload,
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["customer"] == customer_a.id

    # Customer B still has no measurements.
    list_b = client.get(measurements_url(customer_b.id), **_auth(staff))
    assert list_b.json() == []


def test_customer_serializer_does_not_expose_other_customer_measurements(client, staff):
    customer_a = create_customer(full_name="A", mobile_number="9000000001")
    client.post(
        measurements_url(customer_a.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )

    detail = client.get(f"/api/v1/customers/{customer_a.id}/", **_auth(staff))
    assert detail.status_code == 200
    assert "measurements" not in detail.json()
