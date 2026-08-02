"""Customer validation tests."""

import pytest

from apps.customers.tests.helpers import (
    create_customer,
    customer_detail_url,
    customer_list_url,
    make_staff,
    valid_customer_payload,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(staff):
    from apps.authentication.tests.helpers import auth_header

    return {"HTTP_AUTHORIZATION": auth_header(staff)["HTTP_AUTHORIZATION"]}


def _create(client, staff, payload):
    return client.post(
        customer_list_url(), payload, content_type="application/json", **_auth(staff)
    )


def _patch(client, staff, customer_id, payload):
    return client.patch(
        customer_detail_url(customer_id),
        payload,
        content_type="application/json",
        **_auth(staff),
    )


def test_missing_full_name_is_rejected(client, staff):
    payload = valid_customer_payload()
    del payload["full_name"]
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert "full_name" in response.json()["error"]["details"]


def test_blank_full_name_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["full_name"] = "   "
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "full_name" in response.json()["error"]["details"]


def test_invalid_mobile_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["mobile_number"] = "12345"
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_alphabetic_mobile_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["mobile_number"] = "98765abcde"
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_invalid_alternate_mobile_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["alternate_mobile_number"] = "not-a-number"
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "alternate_mobile_number" in response.json()["error"]["details"]


def test_alternate_mobile_equal_to_primary_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["alternate_mobile_number"] = payload["mobile_number"]
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "alternate_mobile_number" in response.json()["error"]["details"]


def test_full_name_too_long_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["full_name"] = "A" * 201
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "full_name" in response.json()["error"]["details"]


def test_mobile_too_long_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["mobile_number"] = "+" + "9" * 16
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_address_too_long_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["address"] = "A" * 1001
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "address" in response.json()["error"]["details"]


def test_notes_too_long_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["notes"] = "A" * 2001
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "notes" in response.json()["error"]["details"]


def test_valid_customer_is_accepted(client, staff):
    response = _create(client, staff, valid_customer_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Ravi Kumar"
    assert data["mobile_number"] == "9876543210"
    assert data["is_active"] is True
    assert "created_at" in data
    assert "updated_at" in data


def test_valid_customer_with_only_required_fields(client, staff):
    payload = {
        "full_name": "Sita Sharma",
        "mobile_number": "+919876543210",
    }
    response = _create(client, staff, payload)
    assert response.status_code == 201
    assert response.json()["alternate_mobile_number"] == ""


def test_international_mobile_prefix_is_accepted(client, staff):
    payload = valid_customer_payload()
    payload["mobile_number"] = "+919876543210"
    response = _create(client, staff, payload)
    assert response.status_code == 201


def test_patch_rejects_invalid_mobile(client, staff):
    customer = create_customer()
    response = _patch(client, staff, customer.id, {"mobile_number": "12"})
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_patch_updates_fields(client, staff):
    customer = create_customer()
    response = _patch(
        client,
        staff,
        customer.id,
        {"full_name": "Renamed", "notes": "Updated notes"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Renamed"
    assert data["notes"] == "Updated notes"


def test_patch_cannot_change_is_active(client, staff):
    customer = create_customer()
    response = _patch(client, staff, customer.id, {"is_active": False})
    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.is_active is True
