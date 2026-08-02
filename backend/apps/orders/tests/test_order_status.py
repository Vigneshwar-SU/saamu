"""Order status lifecycle tests: valid transitions, invalid transitions,
terminal-state protection, cancellation, collected_at and status history."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.orders.models import Order, OrderStatus, OrderStatusHistory
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


def _create_order(client, staff, customer):
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
    return response.json()


def _transition(client, staff, order_id, status):
    return client.post(
        f"/api/v1/orders/{order_id}/status/",
        {"status": status},
        content_type="application/json",
        **_auth(staff),
    )


def test_create_records_initial_new_history(client, staff, customer):
    order = _create_order(client, staff, customer)
    history = OrderStatusHistory.objects.filter(order_id=order["id"])
    assert history.count() == 1
    entry = history.first()
    assert entry.from_status is None
    assert entry.to_status == OrderStatus.NEW
    assert entry.changed_by_id == staff.id


def test_full_valid_chain(client, staff, customer):
    order = _create_order(client, staff, customer)
    chain = ["CUTTING", "STITCHING", "READY", "COLLECTED"]
    for target in chain:
        response = _transition(client, staff, order["id"], target)
        assert response.status_code == 200, response.json()
        assert response.json()["order"]["status"] == target
        assert response.json()["order"]["collected_at"] is None or target == "COLLECTED"

    final = client.get(order_detail_url(order["id"]), **_auth(staff)).json()
    assert final["status"] == "COLLECTED"
    assert final["collected_at"] is not None
    assert Order.objects.get(pk=order["id"]).collected_at is not None


def test_history_records_every_transition(client, staff, customer):
    order = _create_order(client, staff, customer)
    for target in ["CUTTING", "STITCHING", "READY", "COLLECTED"]:
        _transition(client, staff, order["id"], target)
    history = OrderStatusHistory.objects.filter(order_id=order["id"]).order_by(
        "changed_at", "id"
    )
    assert list(history.values_list("from_status", "to_status")) == [
        (None, "NEW"),
        ("NEW", "CUTTING"),
        ("CUTTING", "STITCHING"),
        ("STITCHING", "READY"),
        ("READY", "COLLECTED"),
    ]


def test_skip_transition_rejected(client, staff, customer):
    order = _create_order(client, staff, customer)
    response = _transition(client, staff, order["id"], "READY")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.NEW


def test_backward_transition_rejected(client, staff, customer):
    order = _create_order(client, staff, customer)
    _transition(client, staff, order["id"], "CUTTING")
    response = _transition(client, staff, order["id"], "NEW")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_cancellation_from_workflow_states(client, staff, customer):
    order = _create_order(client, staff, customer)
    _transition(client, staff, order["id"], "CUTTING")
    response = _transition(client, staff, order["id"], "CANCELLED")
    assert response.status_code == 200
    assert response.json()["order"]["status"] == "CANCELLED"
    assert response.json()["order"]["collected_at"] is None


def test_cannot_transition_from_collected(client, staff, customer):
    order = _create_order(client, staff, customer)
    for target in ["CUTTING", "STITCHING", "READY", "COLLECTED"]:
        _transition(client, staff, order["id"], target)
    response = _transition(client, staff, order["id"], "READY")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.COLLECTED


def test_cannot_transition_from_cancelled(client, staff, customer):
    order = _create_order(client, staff, customer)
    _transition(client, staff, order["id"], "CANCELLED")
    response = _transition(client, staff, order["id"], "NEW")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert Order.objects.get(pk=order["id"]).status == OrderStatus.CANCELLED


def test_invalid_status_value_rejected(client, staff, customer):
    order = _create_order(client, staff, customer)
    response = _transition(client, staff, order["id"], "GARBAGE")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
