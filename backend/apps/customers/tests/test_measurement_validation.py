"""Measurement validation tests: garment types, numeric ranges, required fields."""

import pytest

from apps.customers.tests.helpers import (
    create_customer,
    make_staff,
    measurements_url,
    valid_pant_payload,
    valid_shirt_payload,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def customer():
    return create_customer()


def _auth(staff):
    from apps.authentication.tests.helpers import auth_header

    return {"HTTP_AUTHORIZATION": auth_header(staff)["HTTP_AUTHORIZATION"]}


def _create(client, staff, customer, payload):
    return client.post(
        measurements_url(customer.id),
        payload,
        content_type="application/json",
        **_auth(staff),
    )


def test_unsupported_garment_type_is_rejected(client, staff, customer):
    payload = valid_shirt_payload()
    payload["garment_type"] = "KURTA"
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "garment_type" in response.json()["error"]["details"]


def test_missing_required_shirt_field_is_rejected(client, staff, customer):
    payload = valid_shirt_payload()
    del payload["chest_circumference"]
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "chest_circumference" in response.json()["error"]["details"]


def test_missing_required_pant_field_is_rejected(client, staff, customer):
    payload = valid_pant_payload()
    del payload["length"]
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "length" in response.json()["error"]["details"]


def test_negative_value_is_rejected(client, staff, customer):
    payload = valid_shirt_payload()
    payload["chest_circumference"] = -5
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "chest_circumference" in response.json()["error"]["details"]


def test_zero_value_is_rejected(client, staff, customer):
    payload = valid_shirt_payload()
    payload["chest_circumference"] = 0
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "chest_circumference" in response.json()["error"]["details"]


def test_oversized_value_is_rejected(client, staff, customer):
    payload = valid_shirt_payload()
    payload["chest_circumference"] = 301.0
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "chest_circumference" in response.json()["error"]["details"]


def test_non_numeric_value_is_rejected(client, staff, customer):
    payload = valid_shirt_payload()
    payload["chest_circumference"] = "wide"
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "chest_circumference" in response.json()["error"]["details"]


def test_wrong_garment_field_is_rejected(client, staff, customer):
    payload = valid_pant_payload()
    payload["neck_circumference"] = 15.5
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "neck_circumference" in response.json()["error"]["details"]


def test_notes_too_long_is_rejected(client, staff, customer):
    payload = valid_shirt_payload()
    payload["notes"] = "A" * 2001
    response = _create(client, staff, customer, payload)
    assert response.status_code == 400
    assert "notes" in response.json()["error"]["details"]


def test_valid_shirt_measurement_is_accepted(client, staff, customer):
    response = _create(client, staff, customer, valid_shirt_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["garment_type"] == "SHIRT"
    assert data["neck_circumference"] == 15.5
    assert data["chest_circumference"] == 40.0
    assert data["version"] == 1
    assert data["is_current"] is True
    assert data["customer"] == customer.id


def test_valid_pant_measurement_is_accepted(client, staff, customer):
    response = _create(client, staff, customer, valid_pant_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["garment_type"] == "PANT"
    assert data["hip_circumference"] == 40.0
    assert data["length"] == 41.0


def test_optional_shirt_fields_may_be_omitted(client, staff, customer):
    payload = valid_shirt_payload()
    del payload["sleeve_circumference"]
    del payload["cuff_circumference"]
    response = _create(client, staff, customer, payload)
    assert response.status_code == 201
    assert response.json()["sleeve_circumference"] is None
    assert response.json()["cuff_circumference"] is None


def test_optional_pant_fields_may_be_omitted(client, staff, customer):
    payload = valid_pant_payload()
    del payload["thigh_circumference"]
    del payload["knee_circumference"]
    del payload["bottom_circumference"]
    response = _create(client, staff, customer, payload)
    assert response.status_code == 201
