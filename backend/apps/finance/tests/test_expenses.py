"""Expense record API tests: RBAC, validation, filters and history."""

from datetime import date, timedelta

import pytest

from apps.customers.tests.helpers import auth_header
from apps.finance.models import Expense
from apps.finance.tests.helpers import (
    create_expense,
    expense_detail_url,
    expenses_list_url,
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
        "category": Expense.Category.MATERIAL,
        "amount": "100.00",
        "expense_date": str(TODAY),
        "payment_method": Expense.Method.CASH,
        "description": "Fabric purchased.",
        "reference": "INV-001",
    }
    payload.update(extra)
    return payload


def test_anonymous_denied(client):
    assert client.get(expenses_list_url()).status_code == 401
    assert (
        client.post(
            expenses_list_url(),
            _valid_payload(),
            content_type="application/json",
        ).status_code
        == 401
    )


def test_staff_can_create_expense(client, staff):
    response = client.post(
        expenses_list_url(),
        _valid_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == Expense.Category.MATERIAL
    assert data["amount"] == 100.0
    assert data["category_display"] == "Material"
    assert data["recorded_by_name"] == staff.username


def test_recorded_by_is_never_accepted_from_client(client, staff):
    other = make_staff(username="other_expense_staff")
    response = client.post(
        expenses_list_url(),
        _valid_payload(recorded_by=other.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    record = Expense.objects.get(pk=response.json()["id"])
    assert record.recorded_by_id == staff.id


def test_owner_can_read_expenses(client, owner, staff):
    expense = create_expense(amount="100.00")
    create_expense(amount="50.00", category=Expense.Category.RENT)

    response = client.get(expenses_list_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 2

    response = client.get(expense_detail_url(expense.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["amount"] == 100.0


def test_owner_cannot_create_expense(client, owner):
    response = client.post(
        expenses_list_url(),
        _valid_payload(),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_expense_amount_must_be_positive(client, staff):
    for amount in ("0", "-1", "0.00"):
        response = client.post(
            expenses_list_url(),
            _valid_payload(amount=amount),
            content_type="application/json",
            **_auth(staff),
        )
        assert response.status_code == 400, amount


def test_expense_requires_category_and_date(client, staff):
    response = client.post(
        expenses_list_url(),
        {"amount": "100.00"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    body = response.json()
    assert "category" in body["error"]["details"]
    assert "expense_date" in body["error"]["details"]


def test_expense_invalid_category_rejected(client, staff):
    response = client.post(
        expenses_list_url(),
        _valid_payload(category="BOGUS"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_expense_requires_payment_method(client, staff):
    response = client.post(
        expenses_list_url(),
        _valid_payload(payment_method=""),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    body = response.json()
    assert "payment_method" in body["error"]["details"]


def test_expense_invalid_payment_method_rejected(client, staff):
    response = client.post(
        expenses_list_url(),
        _valid_payload(payment_method="CHEQUE"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_expense_records_payment_method_and_display(client, staff):
    response = client.post(
        expenses_list_url(),
        _valid_payload(payment_method=Expense.Method.BANK_TRANSFER),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["payment_method"] == Expense.Method.BANK_TRANSFER
    assert data["payment_method_display"] == "Bank Transfer"


def test_expense_filters(client, staff):
    create_expense(amount="100.00", expense_date=TODAY)
    create_expense(
        amount="200.00",
        expense_date=TODAY - timedelta(days=5),
        category=Expense.Category.RENT,
    )

    response = client.get(
        expenses_list_url(),
        {"date_from": str(TODAY - timedelta(days=1)), "date_to": str(TODAY)},
        **_auth(staff),
    )
    assert response.json()["count"] == 1

    response = client.get(expenses_list_url(), {"category": "RENT"}, **_auth(staff))
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["category"] == "RENT"

    response = client.get(expenses_list_url(), {"category": "BOGUS"}, **_auth(staff))
    assert response.status_code == 400


def test_expense_payment_method_filter(client, staff):
    create_expense(amount="100.00", payment_method=Expense.Method.CASH)
    create_expense(amount="200.00", payment_method=Expense.Method.UPI)

    response = client.get(
        expenses_list_url(), {"payment_method": "UPI"}, **_auth(staff)
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["payment_method"] == "UPI"

    response = client.get(
        expenses_list_url(), {"payment_method": "CHEQUE"}, **_auth(staff)
    )
    assert response.status_code == 400


def test_expense_inclusive_date_boundaries(client, staff):
    create_expense(amount="100.00", expense_date=TODAY)
    create_expense(amount="200.00", expense_date=TODAY + timedelta(days=2))

    response = client.get(
        expenses_list_url(),
        {"date_from": str(TODAY), "date_to": str(TODAY + timedelta(days=2))},
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_expense_pagination(client, staff):
    for index in range(25):
        create_expense(
            amount=f"{index + 1}.00",
            expense_date=TODAY - timedelta(days=index),
        )
    response = client.get(expenses_list_url(), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 25
    assert len(response.json()["results"]) == 20
    assert response.json()["next"] is not None


def test_expense_no_physical_delete_and_no_update(client, staff):
    expense = create_expense(amount="100.00")
    expense_id = expense.id

    assert (
        client.delete(expense_detail_url(expense_id), **_auth(staff)).status_code == 405
    )
    assert (
        client.patch(
            expense_detail_url(expense_id), {"amount": "10.00"}, **_auth(staff)
        ).status_code
        == 405
    )
    assert (
        client.put(
            expense_detail_url(expense_id), {"amount": "10.00"}, **_auth(staff)
        ).status_code
        == 405
    )

    assert Expense.objects.filter(pk=expense_id).exists()
    assert Expense.objects.get(pk=expense_id).amount == 100.0
