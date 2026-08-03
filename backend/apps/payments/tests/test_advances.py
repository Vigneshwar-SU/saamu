"""Salary advance API tests: RBAC, filters, history and immutability."""

from datetime import date, timedelta

import pytest
from django.utils import timezone

from apps.customers.tests.helpers import auth_header
from apps.payments.models import SalaryAdvance
from apps.payments.tests.helpers import (
    advance_url,
    advances_url,
    create_advance,
    create_finalized_entry,
    make_owner,
    make_staff,
)
from apps.tailors.tests.helpers import create_tailor

pytestmark = pytest.mark.django_db

TODAY = date.today()


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def test_anonymous_denied(client):
    assert client.get(advances_url()).status_code == 401
    assert (
        client.post(
            advances_url(),
            {"tailor": 1, "amount": "500.00", "advance_date": str(TODAY)},
            content_type="application/json",
        ).status_code
        == 401
    )


def test_staff_can_create_advance(client, staff):
    tailor = create_tailor()
    response = client.post(
        advances_url(),
        {
            "tailor": tailor.id,
            "amount": "500.00",
            "advance_date": str(TODAY),
            "notes": "Advance for fabric purchase.",
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "OUTSTANDING"
    assert data["amount"] == 500.0
    assert data["tailor"]["id"] == tailor.id
    assert data["recorded_by_name"] == staff.username


def test_owner_can_read_advances(client, owner, staff):
    tailor = create_tailor()
    advance = create_advance(tailor, amount="500.00")
    create_advance(tailor, amount="250.00", status=SalaryAdvance.Status.DEDUCTED)

    response = client.get(advances_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 2

    response = client.get(advance_url(advance.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["amount"] == 500.0


def test_owner_cannot_create_advance(client, owner):
    tailor = create_tailor()
    response = client.post(
        advances_url(),
        {"tailor": tailor.id, "amount": "500.00", "advance_date": str(TODAY)},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_advance_amount_must_be_positive(client, staff):
    tailor = create_tailor()
    for amount in ("0", "-1", "0.00"):
        response = client.post(
            advances_url(),
            {"tailor": tailor.id, "amount": amount, "advance_date": str(TODAY)},
            content_type="application/json",
            **_auth(staff),
        )
        assert response.status_code == 400, amount


def test_advance_filters(client, staff):
    tailor = create_tailor()
    other = create_tailor("Other Tailor")
    create_advance(tailor, amount="500.00", advance_date=TODAY)
    create_advance(
        other,
        amount="300.00",
        advance_date=TODAY - timedelta(days=2),
        status=SalaryAdvance.Status.DEDUCTED,
    )

    response = client.get(advances_url(), {"tailor": tailor.id}, **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["tailor"]["id"] == tailor.id

    response = client.get(advances_url(), {"status": "DEDUCTED"}, **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["status"] == "DEDUCTED"

    response = client.get(
        advances_url(),
        {"date_from": str(TODAY - timedelta(days=1)), "date_to": str(TODAY)},
        **_auth(staff),
    )
    assert response.json()["count"] == 1

    response = client.get(advances_url(), {"status": "BOGUS"}, **_auth(staff))
    assert response.status_code == 400


def test_archived_tailor_advance_history_visible(client, staff):
    tailor = create_tailor()
    advance = create_advance(tailor, amount="500.00")

    response = client.post(f"/api/v1/tailors/{tailor.id}/archive/", **_auth(staff))
    assert response.status_code == 200

    response = client.get(advance_url(advance.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["tailor"]["is_active"] is False


def test_no_physical_delete_and_no_update(client, staff):
    tailor = create_tailor()
    advance = create_advance(tailor, amount="500.00")
    advance_id = advance.id

    assert client.delete(advance_url(advance_id), **_auth(staff)).status_code == 405
    assert (
        client.patch(
            advance_url(advance_id), {"amount": "10.00"}, **_auth(staff)
        ).status_code
        == 405
    )
    assert (
        client.put(
            advance_url(advance_id), {"amount": "10.00"}, **_auth(staff)
        ).status_code
        == 405
    )

    assert SalaryAdvance.objects.filter(pk=advance_id).exists()
    assert SalaryAdvance.objects.get(pk=advance_id).amount == 500.0
