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


def test_duplicate_mobile_is_rejected(client, staff):
    create_customer()
    response = _create(client, staff, valid_customer_payload())
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "already exists" in error["message"]
    assert "mobile_number" in error["details"]


def test_duplicate_mobile_with_different_format_is_rejected(client, staff):
    create_customer()
    payload = valid_customer_payload()
    payload["mobile_number"] = "+919876543210"
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_duplicate_mobile_with_trunk_prefix_is_rejected(client, staff):
    create_customer()
    payload = valid_customer_payload()
    payload["mobile_number"] = "0 98765 43210"
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_duplicate_alternate_mobile_is_rejected(client, staff):
    create_customer(full_name="Existing", mobile_number="9000000001", alternate_mobile_number="9876543210")
    response = _create(client, staff, valid_customer_payload())
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_new_customer_matching_alternate_of_another_is_rejected(client, staff):
    create_customer(full_name="Existing", mobile_number="9000000001", alternate_mobile_number="9876543210")
    payload = valid_customer_payload()
    payload["alternate_mobile_number"] = ""
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_alternate_mobile_equal_to_primary_different_format_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["mobile_number"] = "9876543210"
    payload["alternate_mobile_number"] = "+919876543210"
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "alternate_mobile_number" in response.json()["error"]["details"]


def test_same_name_different_mobile_is_allowed(client, staff):
    payload = valid_customer_payload()
    payload["mobile_number"] = "9000000001"
    assert _create(client, staff, payload).status_code == 201

    payload["mobile_number"] = "9000000002"
    response = _create(client, staff, payload)
    assert response.status_code == 201
    assert response.json()["full_name"] == "Ravi Kumar"


def test_patch_keeping_pre_existing_duplicate_mobile_is_allowed(client, staff):
    create_customer()
    other = create_customer(full_name="Duplicate", mobile_number="9876543210")
    response = _patch(
        client,
        staff,
        other.id,
        {"full_name": "Renamed", "mobile_number": "9876543210"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Renamed"


def test_patch_changing_to_existing_mobile_is_rejected(client, staff):
    create_customer(full_name="A", mobile_number="9000000001")
    other = create_customer(full_name="B", mobile_number="9000000002")
    response = _patch(client, staff, other.id, {"mobile_number": "9000000001"})
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_name_with_only_numbers_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["full_name"] = "123456"
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "full_name" in response.json()["error"]["details"]


def test_name_with_only_symbols_is_rejected(client, staff):
    payload = valid_customer_payload()
    payload["full_name"] = "@#$%"
    response = _create(client, staff, payload)
    assert response.status_code == 400
    assert "full_name" in response.json()["error"]["details"]
