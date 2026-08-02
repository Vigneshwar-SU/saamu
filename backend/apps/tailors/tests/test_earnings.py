"""Earnings computation, filtering and summary tests."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.customers.tests.helpers import auth_header
from apps.tailors.models import WorkAssignment
from apps.tailors.tests.helpers import (
    create_assignment,
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_owner,
    make_staff,
    tailor_earnings_summary_url,
    tailor_earnings_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


@pytest.fixture
def completed_assignment():
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 6, "PANT": 2})
    tailor = create_tailor("Earn Tailor")
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")
    create_piece_rate(garment_type="PANT", rate_per_piece="200.00")

    shirt_item = get_order_item(order, "SHIRT")
    pant_item = get_order_item(order, "PANT")

    shirt = create_assignment(
        tailor,
        shirt_item,
        assigned_quantity=4,
        status=WorkAssignment.Status.COMPLETED,
        completed_quantity=4,
        rate_per_piece_snapshot="150.00",
    )
    pant = create_assignment(
        tailor,
        pant_item,
        assigned_quantity=2,
        status=WorkAssignment.Status.COMPLETED,
        completed_quantity=2,
        rate_per_piece_snapshot="200.00",
    )
    for assignment in (shirt, pant):
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=["completed_at"])
    return {"tailor": tailor, "shirt": shirt, "pant": pant}


def test_earnings_summary_and_breakdown(client, staff, completed_assignment):
    tailor = completed_assignment["tailor"]
    response = client.get(tailor_earnings_url(tailor.id), **_auth(staff))
    assert response.status_code == 200
    data = response.json()

    assert data["summary"]["total_completed_quantity"] == 6
    assert data["summary"]["total_earned"] == 1000.0

    breakdown = {b["garment_type"]: b for b in data["garment_breakdown"]}
    assert breakdown["SHIRT"]["completed_quantity"] == 4
    assert breakdown["SHIRT"]["earned_amount"] == 600.0
    assert breakdown["PANT"]["completed_quantity"] == 2
    assert breakdown["PANT"]["earned_amount"] == 400.0


def test_earnings_exclude_not_completed(client, staff, completed_assignment):
    tailor = completed_assignment["tailor"]
    order = completed_assignment["shirt"].order_item.order
    item = get_order_item(order, "SHIRT")
    create_assignment(
        tailor, item, assigned_quantity=1, status=WorkAssignment.Status.IN_PROGRESS
    )

    response = client.get(tailor_earnings_url(tailor.id), **_auth(staff))
    data = response.json()
    assert data["summary"]["total_completed_quantity"] == 6
    assert data["summary"]["total_earned"] == 1000.0


def test_earnings_honor_date_filter(client, staff, completed_assignment):
    tailor = completed_assignment["tailor"]
    assignment = completed_assignment["shirt"]
    assignment.completed_at = timezone.now() - timedelta(days=30)
    assignment.save(update_fields=["completed_at"])

    today = timezone.now().date()
    response = client.get(
        tailor_earnings_url(tailor.id),
        {"date_from": str(today)},
        **_auth(staff),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_completed_quantity"] == 2
    assert data["summary"]["total_earned"] == 400.0


def test_earnings_honor_garment_filter(client, staff, completed_assignment):
    tailor = completed_assignment["tailor"]
    response = client.get(
        tailor_earnings_url(tailor.id),
        {"garment_type": "PANT"},
        **_auth(staff),
    )
    data = response.json()
    assert data["summary"]["total_completed_quantity"] == 2
    assert data["summary"]["total_earned"] == 400.0
    assert len(data["garment_breakdown"]) == 1


def test_earnings_owner_can_read(client, owner, completed_assignment):
    tailor = completed_assignment["tailor"]
    response = client.get(tailor_earnings_url(tailor.id), **_auth(owner))
    assert response.status_code == 200


def test_summary_aggregates_all_tailors(client, staff, completed_assignment):
    tailor = completed_assignment["tailor"]

    customer = create_customer("Another Customer")
    order = create_order_with_items(customer, {"SHIRT": 2})
    other = create_tailor("Other Tailor")
    item = get_order_item(order, "SHIRT")
    create_assignment(
        other,
        item,
        assigned_quantity=2,
        status=WorkAssignment.Status.COMPLETED,
        completed_quantity=2,
        rate_per_piece_snapshot="100.00",
    )

    response = client.get(tailor_earnings_summary_url(), **_auth(staff))
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_completed_quantity"] == 8
    assert data["summary"]["total_earned"] == 1200.0

    by_name = {t["name"]: t for t in data["tailors"]}
    assert by_name["Earn Tailor"]["earned_amount"] == 1000.0
    assert by_name["Other Tailor"]["earned_amount"] == 200.0


def test_summary_includes_outstanding_workload(client, staff, completed_assignment):
    tailor = completed_assignment["tailor"]
    customer = create_customer("Another Customer")
    order = create_order_with_items(customer, {"SHIRT": 3})
    item = get_order_item(order, "SHIRT")
    create_assignment(
        tailor,
        item,
        assigned_quantity=3,
        status=WorkAssignment.Status.IN_PROGRESS,
        completed_quantity=1,
        rate_per_piece_snapshot="150.00",
    )

    response = client.get(tailor_earnings_summary_url(), **_auth(staff))
    data = response.json()
    entry = next(t for t in data["tailors"] if t["name"] == "Earn Tailor")
    assert entry["outstanding_quantity"] == 2


def test_summary_tailor_filter(client, staff, completed_assignment):
    tailor = completed_assignment["tailor"]
    response = client.get(
        tailor_earnings_summary_url(), {"tailor": tailor.id}, **_auth(staff)
    )
    data = response.json()
    assert data["summary"]["total_completed_quantity"] == 6
    assert data["summary"]["total_earned"] == 1000.0


def test_summary_invalid_tailor_rejected(client, staff):
    response = client.get(
        tailor_earnings_summary_url(), {"tailor": 999999}, **_auth(staff)
    )
    assert response.status_code == 400


def test_summary_owner_can_read(client, owner, completed_assignment):
    response = client.get(tailor_earnings_summary_url(), **_auth(owner))
    assert response.status_code == 200


def test_earnings_anonymous_rejected(client, completed_assignment):
    tailor = completed_assignment["tailor"]
    response = client.get(tailor_earnings_url(tailor.id))
    assert response.status_code == 401
