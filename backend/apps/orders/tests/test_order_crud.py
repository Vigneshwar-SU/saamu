"""Order CRUD tests: creation, retrieval, listing, search, filters,
pagination, multi-garment orders and field validation."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.orders.tests.helpers import (
    create_measurement,
    make_owner,
    make_staff,
    order_detail_url,
    order_item_payload,
    order_list_url,
    valid_order_payload,
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


def test_staff_can_create_shirt_order(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
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
    body = response.json()
    assert body["order_number"].startswith("ORD-")
    assert body["status"] == "NEW"
    assert body["customer"]["id"] == customer.id
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["garment_code"] == "SHIRT"
    assert item["measurement_version"] == 1
    assert item["line_total"] == 100.00
    assert body["total_amount"] == 100.00


def test_staff_can_create_multiple_garments(client, staff, customer):
    shirt = create_measurement(customer, garment_type="SHIRT")
    pant = create_measurement(customer, garment_type="PANT")
    response = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [
                order_item_payload("SHIRT", quantity=2, measurement_id=shirt.id),
                order_item_payload(
                    "PANT", quantity=1, unit_price="250.50", measurement_id=pant.id
                ),
            ],
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total_amount"] == 2 * 100.00 + 250.50
    assert len(Order.objects.get(pk=body["id"]).items.all()) == 2


def test_order_number_sequence_is_unique(client, staff, customer):
    first = client.post(
        order_list_url(),
        valid_order_payload(customer),
        content_type="application/json",
        **_auth(staff),
    )
    second = client.post(
        order_list_url(),
        valid_order_payload(customer),
        content_type="application/json",
        **_auth(staff),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["order_number"] != second.json()["order_number"]
    assert Order.objects.count() == 2


def test_staff_can_retrieve_order(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    created = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [order_item_payload("SHIRT", measurement_id=measurement.id)],
        },
        content_type="application/json",
        **_auth(staff),
    ).json()
    response = client.get(order_detail_url(created["id"]), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["order_number"] == created["order_number"]
    assert response.json()["customer"]["id"] == customer.id


def test_list_returns_paginated_results(client, staff, customer):
    for _ in range(25):
        client.post(
            order_list_url(),
            valid_order_payload(customer),
            content_type="application/json",
            **_auth(staff),
        )
    response = client.get(order_list_url(), **_auth(staff))
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 25
    assert len(body["results"]) == 6
    assert body["next"] is not None

    page2 = client.get(order_list_url() + "?page=2", **_auth(staff))
    assert page2.status_code == 200
    assert len(page2.json()["results"]) == 6


def test_search_by_order_number(client, staff, customer):
    created = client.post(
        order_list_url(),
        valid_order_payload(customer),
        content_type="application/json",
        **_auth(staff),
    ).json()
    response = client.get(
        order_list_url() + f"?search={created['order_number']}", **_auth(staff)
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == created["id"]


def test_search_by_customer_name(client, staff, customer):
    client.post(
        order_list_url(),
        valid_order_payload(customer),
        content_type="application/json",
        **_auth(staff),
    )
    response = client.get(
        order_list_url() + f"?search={customer.full_name.split()[0]}", **_auth(staff)
    )
    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_status_filter(client, staff, customer):
    created = client.post(
        order_list_url(),
        valid_order_payload(customer),
        content_type="application/json",
        **_auth(staff),
    ).json()
    response = client.get(order_list_url() + "?status=CUTTING", **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 0

    client.post(
        order_status_url_for(created["id"]),
        {"status": "CUTTING"},
        content_type="application/json",
        **_auth(staff),
    )
    response = client.get(order_list_url() + "?status=CUTTING", **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 1


def order_status_url_for(order_id):
    return f"/api/v1/orders/{order_id}/status/"


def test_invalid_status_filter_rejected(client, staff):
    response = client.get(order_list_url() + "?status=GARBAGE", **_auth(staff))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_date_filters(client, staff, customer):
    client.post(
        order_list_url(),
        valid_order_payload(customer),
        content_type="application/json",
        **_auth(staff),
    )
    response = client.get(
        order_list_url() + "?date_from=2000-01-01&date_to=2099-12-31", **_auth(staff)
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_quantity_must_be_positive(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    response = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [
                order_item_payload("SHIRT", quantity=0, measurement_id=measurement.id)
            ],
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_price_cannot_be_negative(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    response = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [
                order_item_payload(
                    "SHIRT", unit_price="-5.00", measurement_id=measurement.id
                )
            ],
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_expected_delivery_cannot_precede_order_date(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    response = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "order_date": "2026-08-02",
            "expected_delivery_date": "2026-08-01",
            "items": [order_item_payload("SHIRT", measurement_id=measurement.id)],
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_order_requires_at_least_one_item(client, staff, customer):
    response = client.post(
        order_list_url(),
        {"customer": customer.id, "items": []},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_archived_customer_cannot_create_order(client, staff, customer):
    customer.is_active = False
    customer.save(update_fields=["is_active"])
    measurement = create_measurement(customer, garment_type="SHIRT")
    response = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [order_item_payload("SHIRT", measurement_id=measurement.id)],
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_patch_accepts_only_safe_fields(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    created = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [order_item_payload("SHIRT", measurement_id=measurement.id)],
        },
        content_type="application/json",
        **_auth(staff),
    ).json()

    response = client.patch(
        order_detail_url(created["id"]),
        {"notes": "Priority order", "expected_delivery_date": "2026-08-10"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["notes"] == "Priority order"
    assert body["expected_delivery_date"] == "2026-08-10"


def test_patch_rejects_status_assignment(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    created = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [order_item_payload("SHIRT", measurement_id=measurement.id)],
        },
        content_type="application/json",
        **_auth(staff),
    ).json()
    response = client.patch(
        order_detail_url(created["id"]),
        {"status": "READY"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "NEW"


def test_order_cannot_be_deleted(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    created = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [order_item_payload("SHIRT", measurement_id=measurement.id)],
        },
        content_type="application/json",
        **_auth(staff),
    ).json()
    response = client.delete(order_detail_url(created["id"]), **_auth(staff))
    assert response.status_code == 405
    assert Order.objects.filter(pk=created["id"]).exists()


def test_order_item_immutability_of_read_fields(client, staff, customer):
    measurement = create_measurement(customer, garment_type="SHIRT")
    created = client.post(
        order_list_url(),
        {
            "customer": customer.id,
            "items": [
                order_item_payload("SHIRT", quantity=3, measurement_id=measurement.id)
            ],
        },
        content_type="application/json",
        **_auth(staff),
    ).json()
    item = OrderItem.objects.get(pk=created["items"][0]["id"])
    assert item.quantity == 3
    assert item.amount == 3 * 100.00
