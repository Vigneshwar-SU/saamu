"""Order measurement validation tests: measurement selection, version validity,
garment mismatch and incomplete measurements."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.orders.tests.helpers import (
    create_measurement,
    make_staff,
    order_item_payload,
    order_list_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def customer():
    from apps.customers.tests.helpers import create_customer

    return create_customer()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _create(client, staff, customer, items):
    return client.post(
        order_list_url(),
        {"customer": customer.id, "items": items},
        content_type="application/json",
        **_auth(staff),
    )


def test_measurement_is_required_for_each_item(client, staff, customer):
    response = _create(client, staff, customer, [order_item_payload("SHIRT")])
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_missing_measurement_rejected(client, staff, customer):
    response = _create(
        client, staff, customer, [order_item_payload("SHIRT", measurement_id=999999)]
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_measurement_of_another_customer_rejected(client, staff, customer):
    from apps.customers.tests.helpers import create_customer as cc

    other = cc(full_name="Other Person", mobile_number="9999999999")
    measurement = create_measurement(other, garment_type="SHIRT")
    response = _create(
        client,
        staff,
        customer,
        [order_item_payload("SHIRT", measurement_id=measurement.id)],
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_garment_type_mismatch_rejected(client, staff, customer):
    pant_measurement = create_measurement(customer, garment_type="PANT")
    response = _create(
        client,
        staff,
        customer,
        [order_item_payload("SHIRT", measurement_id=pant_measurement.id)],
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_incomplete_measurement_rejected(client, staff, customer):
    measurement = create_measurement(
        customer,
        garment_type="SHIRT",
        neck_circumference=None,
        chest_circumference=None,
    )
    response = _create(
        client,
        staff,
        customer,
        [order_item_payload("SHIRT", measurement_id=measurement.id)],
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_historical_version_can_be_selected(client, staff, customer):
    # Create a v1 that is no longer current, plus a current v2.
    v1 = create_measurement(customer, garment_type="SHIRT", version=1, is_current=False)
    create_measurement(customer, garment_type="SHIRT", version=2, is_current=True)
    response = _create(
        client,
        staff,
        customer,
        [order_item_payload("SHIRT", measurement_id=v1.id)],
    )
    assert response.status_code == 201
    assert response.json()["items"][0]["measurement_version"] == 1
