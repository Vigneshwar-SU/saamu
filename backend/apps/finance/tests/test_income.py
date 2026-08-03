"""Income record API tests: RBAC, validation, filters and history."""

from datetime import date, timedelta

import pytest

from apps.customers.tests.helpers import auth_header
from apps.finance.models import Income
from apps.finance.tests.helpers import (
    create_income,
    income_detail_url,
    income_list_url,
    make_owner,
    make_staff,
)

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


def _valid_payload(**extra):
    payload = {
        "category": Income.Category.ORDER_PAYMENT,
        "amount": "500.00",
        "income_date": str(TODAY),
        "description": "Balance paid on order.",
        "reference": "ORD-2026-0001",
    }
    payload.update(extra)
    return payload


def test_anonymous_denied(client):
    assert client.get(income_list_url()).status_code == 401
    assert (
        client.post(
            income_list_url(),
            _valid_payload(),
            content_type="application/json",
        ).status_code
        == 401
    )


def test_staff_can_create_income(client, staff):
    response = client.post(
        income_list_url(),
        _valid_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == Income.Category.ORDER_PAYMENT
    assert data["amount"] == 500.0
    assert data["category_display"] == "Order Payment"
    assert data["recorded_by_name"] == staff.username


def test_recorded_by_is_never_accepted_from_client(client, staff):
    other = make_staff(username="other_staff")
    response = client.post(
        income_list_url(),
        _valid_payload(recorded_by=other.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    record = Income.objects.get(pk=response.json()["id"])
    assert record.recorded_by_id == staff.id


def test_owner_can_read_incomes(client, owner, staff):
    income = create_income(amount="500.00")
    create_income(amount="250.00", category=Income.Category.OTHER_INCOME)

    response = client.get(income_list_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 2

    response = client.get(income_detail_url(income.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["amount"] == 500.0


def test_owner_cannot_create_income(client, owner):
    response = client.post(
        income_list_url(),
        _valid_payload(),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_income_amount_must_be_positive(client, staff):
    for amount in ("0", "-1", "0.00"):
        response = client.post(
            income_list_url(),
            _valid_payload(amount=amount),
            content_type="application/json",
            **_auth(staff),
        )
        assert response.status_code == 400, amount


def test_income_requires_category_and_date(client, staff):
    response = client.post(
        income_list_url(),
        {"amount": "500.00"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    body = response.json()
    assert "category" in body["error"]["details"]
    assert "income_date" in body["error"]["details"]


def test_income_invalid_category_rejected(client, staff):
    response = client.post(
        income_list_url(),
        _valid_payload(category="BOGUS"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_income_filters(client, staff):
    create_income(amount="500.00", income_date=TODAY)
    create_income(
        amount="250.00",
        income_date=TODAY - timedelta(days=5),
        category=Income.Category.OTHER_INCOME,
    )

    response = client.get(
        income_list_url(),
        {"date_from": str(TODAY - timedelta(days=1)), "date_to": str(TODAY)},
        **_auth(staff),
    )
    assert response.json()["count"] == 1

    response = client.get(
        income_list_url(), {"category": "OTHER_INCOME"}, **_auth(staff)
    )
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["category"] == "OTHER_INCOME"

    response = client.get(income_list_url(), {"category": "BOGUS"}, **_auth(staff))
    assert response.status_code == 400


def test_income_inclusive_date_boundaries(client, staff):
    create_income(amount="100.00", income_date=TODAY)
    create_income(amount="200.00", income_date=TODAY + timedelta(days=2))

    response = client.get(
        income_list_url(),
        {"date_from": str(TODAY), "date_to": str(TODAY + timedelta(days=2))},
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_income_pagination(client, staff):
    for index in range(25):
        create_income(
            amount=f"{index + 1}.00",
            income_date=TODAY - timedelta(days=index),
        )
    response = client.get(income_list_url(), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 25
    assert len(response.json()["results"]) == 20
    assert response.json()["next"] is not None


def test_income_no_physical_delete_and_no_update(client, staff):
    income = create_income(amount="500.00")
    income_id = income.id

    assert (
        client.delete(income_detail_url(income_id), **_auth(staff)).status_code == 405
    )
    assert (
        client.patch(
            income_detail_url(income_id), {"amount": "10.00"}, **_auth(staff)
        ).status_code
        == 405
    )
    assert (
        client.put(
            income_detail_url(income_id), {"amount": "10.00"}, **_auth(staff)
        ).status_code
        == 405
    )

    assert Income.objects.filter(pk=income_id).exists()
    assert Income.objects.get(pk=income_id).amount == 500.0
