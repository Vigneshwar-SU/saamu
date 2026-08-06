"""Expense summary API tests: RBAC, totals and breakdown correctness."""

from datetime import date, timedelta

import pytest

from apps.customers.tests.helpers import auth_header
from apps.finance.models import Expense
from apps.finance.tests.helpers import (
    create_expense,
    expense_summary_url,
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


def test_anonymous_denied(client):
    assert client.get(expense_summary_url()).status_code == 401


def test_owner_can_read_summary(client, owner):
    create_expense(amount="100.00")
    response = client.get(expense_summary_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["expense_count"] == 1


def test_staff_can_read_summary(client, staff):
    create_expense(amount="100.00")
    response = client.get(expense_summary_url(), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["total_expenses"] == 100.0


def test_summary_totals(client, staff):
    create_expense(amount="100.00", category=Expense.Category.MATERIAL)
    create_expense(amount="250.50", category=Expense.Category.RENT)
    create_expense(amount="49.50", category=Expense.Category.RENT)

    response = client.get(expense_summary_url(), **_auth(staff))
    data = response.json()
    assert data["expense_count"] == 3
    assert data["total_expenses"] == 400.0


def test_summary_by_category(client, staff):
    create_expense(amount="100.00", category=Expense.Category.MATERIAL)
    create_expense(amount="250.00", category=Expense.Category.RENT)
    create_expense(amount="50.00", category=Expense.Category.RENT)

    response = client.get(expense_summary_url(), **_auth(staff))
    by_category = response.json()["by_category"]
    categories = {row["category"]: row for row in by_category}
    assert categories[Expense.Category.RENT]["total"] == 300.0
    assert categories[Expense.Category.RENT]["count"] == 2
    assert categories[Expense.Category.RENT]["category_display"] == "Rent"
    assert categories[Expense.Category.MATERIAL]["total"] == 100.0


def test_summary_by_payment_method(client, staff):
    create_expense(amount="100.00", payment_method=Expense.Method.CASH)
    create_expense(amount="200.00", payment_method=Expense.Method.UPI)
    create_expense(amount="50.00", payment_method=Expense.Method.CASH)

    response = client.get(expense_summary_url(), **_auth(staff))
    by_method = response.json()["by_payment_method"]
    methods = {row["payment_method"]: row for row in by_method}
    assert methods[Expense.Method.CASH]["total"] == 150.0
    assert methods[Expense.Method.CASH]["count"] == 2
    assert methods[Expense.Method.CASH]["payment_method_display"] == "Cash"
    assert methods[Expense.Method.UPI]["total"] == 200.0


def test_summary_respects_date_range(client, staff):
    create_expense(amount="100.00", expense_date=TODAY)
    create_expense(amount="200.00", expense_date=TODAY - timedelta(days=10))

    response = client.get(
        expense_summary_url(),
        {"date_from": str(TODAY - timedelta(days=1)), "date_to": str(TODAY)},
        **_auth(staff),
    )
    data = response.json()
    assert data["expense_count"] == 1
    assert data["total_expenses"] == 100.0


def test_summary_respects_category_filter(client, staff):
    create_expense(amount="100.00", category=Expense.Category.MATERIAL)
    create_expense(amount="200.00", category=Expense.Category.RENT)

    response = client.get(expense_summary_url(), {"category": "RENT"}, **_auth(staff))
    data = response.json()
    assert data["expense_count"] == 1
    assert data["total_expenses"] == 200.0


def test_summary_respects_payment_method_filter(client, staff):
    create_expense(amount="100.00", payment_method=Expense.Method.CASH)
    create_expense(amount="200.00", payment_method=Expense.Method.UPI)

    response = client.get(
        expense_summary_url(), {"payment_method": "UPI"}, **_auth(staff)
    )
    data = response.json()
    assert data["expense_count"] == 1
    assert data["total_expenses"] == 200.0


def test_summary_rejects_invalid_filters(client, staff):
    response = client.get(expense_summary_url(), {"category": "BOGUS"}, **_auth(staff))
    assert response.status_code == 400

    response = client.get(
        expense_summary_url(), {"payment_method": "CHEQUE"}, **_auth(staff)
    )
    assert response.status_code == 400

    response = client.get(
        expense_summary_url(),
        {"date_from": str(TODAY), "date_to": str(TODAY - timedelta(days=1))},
        **_auth(staff),
    )
    assert response.status_code == 400
