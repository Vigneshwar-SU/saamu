"""Piece rate configuration tests: CRUD, validation, immutability of history."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.tailors.models import PieceRate
from apps.tailors.tests.helpers import (
    assign_payload,
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_staff,
    piece_rate_url,
    piece_rates_url,
    valid_piece_rate_payload,
    work_assignments_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def test_staff_can_create_piece_rate(client, staff):
    response = client.post(
        piece_rates_url(),
        valid_piece_rate_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["rate_per_piece"] == 150.0


def test_garment_type_is_unique(client, staff):
    create_piece_rate(garment_type="SHIRT")
    response = client.post(
        piece_rates_url(),
        valid_piece_rate_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_negative_rate_rejected(client, staff):
    response = client.post(
        piece_rates_url(),
        valid_piece_rate_payload(rate_per_piece="-10.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_rate_can_be_updated(client, staff):
    rate = create_piece_rate(rate_per_piece="150.00")
    response = client.patch(
        piece_rate_url(rate.id),
        {"rate_per_piece": "175.00"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    rate.refresh_from_db()
    assert str(rate.rate_per_piece) == "175.00"


def test_rate_can_be_deactivated(client, staff):
    rate = create_piece_rate()
    response = client.patch(
        piece_rate_url(rate.id),
        {"is_active": False},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    rate.refresh_from_db()
    assert rate.is_active is False


def test_rates_are_never_deleted(client, staff):
    rate = create_piece_rate()
    response = client.delete(piece_rate_url(rate.id), **_auth(staff))
    assert response.status_code == 405
    assert PieceRate.objects.filter(pk=rate.pk).exists()


def test_list_returns_all_rates(client, staff):
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")
    create_piece_rate(garment_type="PANT", rate_per_piece="200.00")
    response = client.get(piece_rates_url(), **_auth(staff))
    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


def test_assignment_snapshots_rate_at_creation(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")

    response = client.post(
        work_assignments_url(),
        assign_payload(
            tailor, order, get_order_item(order, "SHIRT"), assigned_quantity=2
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assignment = response.json()
    assert assignment["rate_per_piece_snapshot"] == 150.0

    rate = PieceRate.objects.get(garment_type="SHIRT")
    rate.rate_per_piece = "200.00"
    rate.save()

    detail_response = client.get(
        f"/api/v1/work-assignments/{assignment['id']}/", **_auth(staff)
    )
    assert detail_response.json()["rate_per_piece_snapshot"] == 150.0


def test_no_active_rate_blocks_assignment(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 3})
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00", is_active=False)

    response = client.post(
        work_assignments_url(),
        assign_payload(
            tailor, order, get_order_item(order, "SHIRT"), assigned_quantity=2
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "piece rate" in response.json()["error"]["details"]["order_item"]
