"""Measurement snapshot immutability tests: order line items must keep the
measurement values captured at order creation even after the customer's
current measurement is later updated."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.orders.models import OrderItem
from apps.orders.tests.helpers import (
    create_measurement,
    make_staff,
    order_detail_url,
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


def _create(client, staff, customer, measurement):
    response = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [order_item_payload("SHIRT", measurement_id=measurement.id)],
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    return response.json()


def test_snapshot_matches_measurement_at_creation(client, staff, customer):
    measurement = create_measurement(
        customer,
        garment_type="SHIRT",
        neck_circumference=14.5,
        chest_circumference=38.0,
        waist_circumference=32.0,
        shoulder_width=17.0,
        sleeve_length=23.0,
        shirt_length=28.0,
    )
    order = _create(client, staff, customer, measurement)
    item = OrderItem.objects.get(pk=order["items"][0]["id"])
    snapshot = item.measurement_snapshot
    assert snapshot["neck_circumference"] == 14.5
    assert snapshot["chest_circumference"] == 38.0
    assert snapshot["waist_circumference"] == 32.0
    assert snapshot["shoulder_width"] == 17.0
    assert snapshot["sleeve_length"] == 23.0
    assert snapshot["shirt_length"] == 28.0


def test_snapshot_survives_customer_measurement_update(client, staff, customer):
    v1 = create_measurement(
        customer,
        garment_type="SHIRT",
        version=1,
        is_current=False,
        chest_circumference=38.0,
    )
    order = _create(client, staff, customer, v1)
    item = OrderItem.objects.get(pk=order["items"][0]["id"])

    # Customer updates their measurements (new current version).
    v2 = create_measurement(
        customer,
        garment_type="SHIRT",
        version=2,
        is_current=True,
        chest_circumference=44.0,
    )
    customer.save()

    item.refresh_from_db()
    assert item.measurement_snapshot["chest_circumference"] == 38.0

    # API response must reflect the snapshot, not the new measurement.
    body = client.get(order_detail_url(order["id"]), **_auth(staff)).json()
    assert body["items"][0]["measurement_version"] == 1
    assert body["items"][0]["measurement_snapshot"]["chest_circumference"] == 38.0
    assert v2.is_current is True
