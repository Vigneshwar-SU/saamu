"""Dashboard summary API tests: arithmetic, operational metrics and RBAC."""

from datetime import date, timedelta

import pytest

from apps.billing.models import CustomerPayment
from apps.billing.tests.helpers import (
    create_invoice,
)
from apps.billing.tests.helpers import create_payment as create_customer_payment
from apps.customers.tests.helpers import auth_header, create_customer
from apps.finance.models import Expense
from apps.finance.tests.helpers import (
    create_expense,
    dashboard_summary_url,
    make_owner,
    make_staff,
)
from apps.orders.models import OrderStatus
from apps.payments.tests.helpers import (
    create_advance,
    create_finalized_entry,
    create_payment,
)
from apps.tailors.models import WorkAssignment
from apps.tailors.tests.helpers import (
    create_assignment,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
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


def _summary(client, user, **params):
    return client.get(dashboard_summary_url(), params, **_auth(user))


def test_anonymous_denied(client):
    assert client.get(dashboard_summary_url()).status_code == 401


def test_owner_and_staff_can_read_empty_dashboard(client, owner, staff):
    for user in (owner, staff):
        response = _summary(client, user)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["financial"] == {
            "recorded_income": 0.0,
            "recorded_expenses": 0.0,
            "net_recorded_balance": 0.0,
            "payroll_paid": 0.0,
            "salary_advances": 0.0,
            "order_revenue": 0.0,
        }
        assert data["operational"]["order_counts"]["total"] == 0
        assert data["operational"]["garment_quantities"] == {"SHIRT": 0, "PANT": 0}
        assert data["operational"]["workload"]["assigned_quantity"] == 0
        assert data["operational"]["active_customers"] == 0
        assert data["operational"]["active_tailors"] == 0
        assert data["recent_payments"] == []
        assert data["recent_expenses"] == []


def test_dashboard_income_expense_and_net_totals(client, staff):
    invoice = create_invoice()
    create_customer_payment(
        invoice,
        amount="500.00",
        payment_date=TODAY,
        payment_type=CustomerPayment.PaymentType.ADVANCE,
    )
    create_customer_payment(
        invoice,
        amount="250.50",
        payment_date=TODAY,
        payment_type=CustomerPayment.PaymentType.PARTIAL,
    )
    create_expense(amount="100.00", expense_date=TODAY)
    create_expense(amount="50.25", expense_date=TODAY, category=Expense.Category.RENT)

    data = _summary(client, staff).json()["financial"]
    assert data["recorded_income"] == 750.5
    assert data["recorded_expenses"] == 150.25
    assert data["net_recorded_balance"] == 600.25


def test_dashboard_payroll_paid_aggregation(client, staff):
    entry = create_finalized_entry()
    create_payment(entry, amount="300.00", payment_date=TODAY)
    create_payment(entry, amount="200.00", payment_date=TODAY)

    data = _summary(client, staff).json()["financial"]
    assert data["payroll_paid"] == 500.0


def test_dashboard_salary_advances_are_separate_metric(client, staff):
    tailor = create_tailor()
    create_advance(tailor, amount="500.00", advance_date=TODAY)
    create_advance(tailor, amount="250.00", advance_date=TODAY)

    data = _summary(client, staff).json()["financial"]
    assert data["salary_advances"] == 750.0
    assert data["recorded_expenses"] == 0.0


def test_dashboard_order_revenue_distinct_from_recorded_income(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 5, "PANT": 3})
    create_customer_payment(create_invoice(order), amount="500.00", payment_date=TODAY)

    data = _summary(client, staff).json()["financial"]
    assert data["order_revenue"] == 800.0
    assert data["recorded_income"] == 500.0
    assert data["order_revenue"] != data["recorded_income"]


def test_dashboard_order_status_counts(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    create_order_with_items(customer, {"PANT": 1})

    order.status = OrderStatus.READY
    order.save(update_fields=["status", "updated_at"])

    counts = _summary(client, staff).json()["operational"]["order_counts"]
    assert counts["total"] == 2
    assert counts[OrderStatus.NEW] == 1
    assert counts[OrderStatus.READY] == 1
    assert counts[OrderStatus.COLLECTED] == 0


def test_dashboard_garment_quantities(client, staff):
    customer = create_customer()
    other_customer = create_customer("Second Customer")
    create_order_with_items(customer, {"SHIRT": 5, "PANT": 3})
    create_order_with_items(other_customer, {"SHIRT": 2})

    quantities = _summary(client, staff).json()["operational"]["garment_quantities"]
    assert quantities == {"SHIRT": 7, "PANT": 3}


def test_dashboard_tailor_workload(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = create_order_with_items(customer, {"SHIRT": 10})
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")
    item = get_order_item(order, "SHIRT")
    create_assignment(
        tailor,
        item,
        assigned_quantity=10,
        completed_quantity=4,
        status=WorkAssignment.Status.IN_PROGRESS,
        rate_per_piece_snapshot="150.00",
    )

    workload = _summary(client, staff).json()["operational"]["workload"]
    assert workload["assigned_quantity"] == 10
    assert workload["completed_quantity"] == 4
    assert workload["outstanding_quantity"] == 6
    assert workload["earned_amount"] == 600.0


def test_dashboard_active_counts_and_recent_lists(client, staff):
    customer = create_customer()
    create_customer("Archived Customer", is_active=False)
    create_tailor("Active Tailor")
    create_tailor("Archived Tailor", is_active=False)
    payment = create_customer_payment(
        create_invoice(create_order_with_items(customer, {"SHIRT": 1})),
        amount="500.00",
        payment_date=TODAY,
    )
    expense = create_expense(amount="100.00", expense_date=TODAY)

    data = _summary(client, staff).json()
    assert data["operational"]["active_customers"] == 1
    assert data["operational"]["active_tailors"] == 1
    assert data["recent_payments"][0]["id"] == payment.id
    assert data["recent_payments"][0]["amount"] == 500.0
    assert data["recent_expenses"][0]["id"] == expense.id


def test_dashboard_inclusive_date_boundaries(client, staff):
    invoice = create_invoice()
    create_customer_payment(invoice, amount="100.00", payment_date=TODAY)
    create_customer_payment(
        invoice, amount="200.00", payment_date=TODAY + timedelta(days=3)
    )
    create_customer_payment(
        invoice, amount="300.00", payment_date=TODAY - timedelta(days=3)
    )

    data = _summary(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY + timedelta(days=3)),
    ).json()["financial"]
    assert data["recorded_income"] == 300.0


def test_dashboard_date_range_validation(client, staff):
    response = _summary(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY - timedelta(days=1)),
    )
    assert response.status_code == 400


def test_dashboard_invalid_date_returns_400(client, staff):
    response = _summary(client, staff, date_from="not-a-date")
    assert response.status_code == 400


def test_dashboard_is_read_only(client, staff):
    assert client.post(dashboard_summary_url(), {}, **_auth(staff)).status_code in (
        403,
        405,
    )


def test_dashboard_owner_can_read(client, owner, staff):
    create_customer_payment(create_invoice(), amount="500.00", payment_date=TODAY)
    response = _summary(client, owner)
    assert response.status_code == 200
    assert response.json()["financial"]["recorded_income"] == 500.0
