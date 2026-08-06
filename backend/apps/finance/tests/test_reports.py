"""Reports & business-insights summary API tests (Phase 14).

The reports summary is a read-only layer over the authoritative records:
income/refunds reuse the Phase 13 ``build_income_summary`` aggregation,
expenses reuse the Phase 12 ``build_expense_summary`` aggregation, and
orders/customers/tailors are aggregated from their own modules. These tests
assert RBAC, date-filter behavior, arithmetic consistency and that reports
agree with the existing income/expense summaries.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.authentication.tests.helpers import auth_header
from apps.billing.models import CustomerPayment
from apps.billing.tests.helpers import create_invoice
from apps.billing.tests.helpers import create_payment as create_customer_payment
from apps.customers.tests.helpers import create_customer
from apps.finance.models import Expense
from apps.finance.services import (
    build_expense_summary,
    build_income_summary,
    build_reports_summary,
)
from apps.finance.tests.helpers import (
    create_expense,
    make_owner,
    make_staff,
    reports_summary_url,
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
    return client.get(reports_summary_url(), params, **_auth(user))


def _payment(invoice=None, amount="500.00", payment_date=None, **extra):
    return create_customer_payment(
        invoice or create_invoice(),
        amount=amount,
        payment_date=payment_date or TODAY,
        **extra,
    )


def test_anonymous_denied(client):
    assert client.get(reports_summary_url()).status_code == 401


def test_owner_and_staff_can_read_empty_report(client, owner, staff):
    for user in (owner, staff):
        response = _summary(client, user)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["range"] == {"date_from": None, "date_to": None}
        assert data["orders"]["total"] == 0
        assert data["orders"]["revenue"] == 0.0
        assert data["orders"]["status_distribution"]["total"] == 0
        assert data["orders"]["garment_quantities"] == {"SHIRT": 0, "PANT": 0}
        assert data["customers"] == {
            "active_customers": 0,
            "new_customers": 0,
            "customers_with_orders": 0,
        }
        assert data["tailors"]["active_tailors"] == 0
        assert data["tailors"]["workload"]["assigned_quantity"] == 0
        assert data["financial"]["income"]["total_income"] == 0.0
        assert data["financial"]["expenses"]["total_expenses"] == 0.0
        assert data["financial"]["net_position"] == 0.0


def test_reports_are_read_only(client, staff):
    url = reports_summary_url()
    assert client.post(url, {}, **_auth(staff)).status_code in (403, 405)
    assert client.put(url, {}, **_auth(staff)).status_code in (403, 405)
    assert client.patch(url, {}, **_auth(staff)).status_code in (403, 405)
    assert client.delete(url, **_auth(staff)).status_code in (403, 405)


def test_order_counts_and_status_distribution(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 2})
    create_order_with_items(customer, {"PANT": 1})

    order.status = OrderStatus.READY
    order.save(update_fields=["status", "updated_at"])

    data = _summary(client, staff).json()
    distribution = data["orders"]["status_distribution"]
    assert distribution["total"] == 2
    assert distribution[OrderStatus.NEW] == 1
    assert distribution[OrderStatus.READY] == 1
    assert distribution[OrderStatus.COLLECTED] == 0
    assert data["orders"]["total"] == 2


def test_order_revenue_and_garment_quantities(client, staff):
    customer = create_customer()
    create_order_with_items(customer, {"SHIRT": 5, "PANT": 3})
    create_order_with_items(create_customer("Second Customer"), {"SHIRT": 2})

    data = _summary(client, staff).json()
    assert data["orders"]["garment_quantities"] == {"SHIRT": 7, "PANT": 3}
    assert data["orders"]["revenue"] == 1000.0
    assert data["financial"]["order_revenue"] == 1000.0


def test_orders_honor_date_filter(client, staff):
    customer = create_customer()
    create_order_with_items(customer, {"SHIRT": 1})
    create_order_with_items(customer, {"PANT": 1})

    order = customer.orders.first()
    order.order_date = TODAY - timedelta(days=5)
    order.save(update_fields=["order_date", "updated_at"])

    data = _summary(client, staff).json()
    assert data["orders"]["total"] == 2

    data = _summary(client, staff, date_from=str(TODAY), date_to=str(TODAY)).json()
    assert data["orders"]["total"] == 1


def test_customers_metrics_against_database(client, staff):
    customer = create_customer()
    create_customer("Browsing Customer")
    create_customer("Archived Customer", is_active=False)
    create_customer("Archived Other", is_active=False)

    create_order_with_items(customer, {"SHIRT": 1})

    data = _summary(client, staff).json()
    assert data["customers"]["active_customers"] == 2
    assert data["customers"]["new_customers"] == 4
    assert data["customers"]["customers_with_orders"] == 1


def test_customers_new_in_range(client, staff):
    create_customer("Today Customer")
    older = create_customer("Older Customer")
    older.created_at = older.created_at - timedelta(days=10)
    older.save(update_fields=["created_at"])

    data = _summary(client, staff, date_from=str(TODAY), date_to=str(TODAY)).json()
    assert data["customers"]["new_customers"] == 1


def test_tailor_workload_matches_assignment_data(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")
    order = create_order_with_items(customer, {"SHIRT": 10})
    item = get_order_item(order, "SHIRT")
    create_assignment(
        tailor,
        item,
        assigned_quantity=10,
        completed_quantity=4,
        status=WorkAssignment.Status.IN_PROGRESS,
        rate_per_piece_snapshot="150.00",
    )

    workload = _summary(client, staff).json()["tailors"]["workload"]
    assert workload["assigned_quantity"] == 10
    assert workload["completed_quantity"] == 4
    assert workload["outstanding_quantity"] == 6
    assert workload["earned_amount"] == 600.0
    assert workload == build_reports_summary()["tailors"]["workload"]


def test_income_derived_from_customer_payments(client, staff):
    _payment(amount="500.00", payment_type=CustomerPayment.PaymentType.ADVANCE)
    _payment(amount="250.50", payment_type=CustomerPayment.PaymentType.PARTIAL)

    data = _summary(client, staff).json()["financial"]["income"]
    assert data["total_income"] == 750.5
    assert data["payment_count"] == 2
    assert data["refund_count"] == 0


def test_refunds_reduce_net_income(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="1000.00",
        payment_type=CustomerPayment.PaymentType.FINAL,
    )
    _payment(
        invoice=invoice,
        amount="300.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    income = _summary(client, staff).json()["financial"]["income"]
    assert income["total_income"] == 700.0
    assert income["refund_count"] == 1
    assert income["total_refunds"] == 300.0
    assert income["total_income"] > 0

    refund_row = next(
        row for row in income["by_payment_type"] if row["payment_type"] == "REFUND"
    )
    assert refund_row["total"] == -300.0


def test_refund_never_becomes_positive_income(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="500.00",
        payment_type=CustomerPayment.PaymentType.PARTIAL,
    )
    _payment(
        invoice=invoice,
        amount="300.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    income = _summary(client, staff).json()["financial"]["income"]
    assert income["total_income"] == 200.0
    assert income["total_income"] < 500.0


def test_expenses_from_expense_records(client, staff):
    create_expense(amount="100.00", expense_date=TODAY)
    create_expense(amount="50.25", expense_date=TODAY, category=Expense.Category.RENT)

    expenses = _summary(client, staff).json()["financial"]["expenses"]
    assert expenses["total_expenses"] == 150.25
    assert expenses["expense_count"] == 2


def test_net_position_is_mathematically_consistent(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="1000.00",
        payment_type=CustomerPayment.PaymentType.FINAL,
    )
    _payment(
        invoice=invoice,
        amount="250.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )
    create_expense(amount="300.00", expense_date=TODAY)

    data = _summary(client, staff).json()["financial"]
    assert data["income"]["total_income"] == 750.0
    assert data["expenses"]["total_expenses"] == 300.0
    assert data["net_position"] == 450.0
    assert data["net_position"] == round(
        data["income"]["total_income"] - data["expenses"]["total_expenses"], 2
    )


def test_report_income_agrees_with_income_summary(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="1000.00",
        payment_date=TODAY,
        payment_type=CustomerPayment.PaymentType.FINAL,
    )
    _payment(
        invoice=invoice,
        amount="250.00",
        payment_date=TODAY,
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    report = _summary(client, staff).json()["financial"]["income"]
    summary = build_income_summary(TODAY, TODAY)
    summary.pop("success", None)
    assert (
        report
        == summary
        == {
            "total_income": 750.0,
            "payment_count": 1,
            "refund_count": 1,
            "total_refunds": 250.0,
            "by_payment_method": report["by_payment_method"],
            "by_payment_type": report["by_payment_type"],
        }
    )


def test_report_expenses_agree_with_expense_summary(client, staff):
    create_expense(amount="100.00", expense_date=TODAY)
    create_expense(amount="50.25", expense_date=TODAY, category=Expense.Category.RENT)

    report = _summary(client, staff).json()["financial"]["expenses"]
    summary = build_expense_summary(TODAY, TODAY)
    summary.pop("success", None)
    assert report == summary
    assert report["total_expenses"] == 150.25


def test_no_filter_includes_all_records(client, staff):
    customer = create_customer()
    _payment(amount="100.00", payment_date=TODAY - timedelta(days=10))
    _payment(amount="200.00", payment_date=TODAY + timedelta(days=10))
    create_expense(amount="50.00", expense_date=TODAY - timedelta(days=10))
    create_order_with_items(customer, {"SHIRT": 1})

    data = _summary(client, staff).json()
    assert data["financial"]["income"]["total_income"] == 300.0
    assert data["financial"]["expenses"]["total_expenses"] == 50.0
    assert data["orders"]["total"] == 3


def test_date_from_filter(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00", payment_date=TODAY - timedelta(days=2))
    _payment(invoice=invoice, amount="200.00", payment_date=TODAY)

    data = _summary(client, staff, date_from=str(TODAY)).json()
    assert data["financial"]["income"]["total_income"] == 200.0


def test_date_to_filter(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00", payment_date=TODAY)
    _payment(invoice=invoice, amount="200.00", payment_date=TODAY + timedelta(days=2))

    data = _summary(client, staff, date_to=str(TODAY)).json()
    assert data["financial"]["income"]["total_income"] == 100.0


def test_combined_date_range_filters_all_sections(client, staff):
    customer = create_customer()
    _payment(amount="100.00", payment_date=TODAY)
    _payment(amount="200.00", payment_date=TODAY + timedelta(days=3))
    _payment(amount="300.00", payment_date=TODAY - timedelta(days=3))
    create_expense(amount="40.00", expense_date=TODAY)
    create_expense(amount="60.00", expense_date=TODAY + timedelta(days=4))
    create_order_with_items(customer, {"SHIRT": 1})

    data = _summary(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY + timedelta(days=3)),
    ).json()
    assert data["financial"]["income"]["total_income"] == 300.0
    assert data["financial"]["expenses"]["total_expenses"] == 40.0
    assert data["orders"]["total"] == 4


def test_inclusive_date_boundaries(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00", payment_date=TODAY)
    _payment(invoice=invoice, amount="200.00", payment_date=TODAY + timedelta(days=3))

    data = _summary(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY + timedelta(days=3)),
    ).json()
    assert data["financial"]["income"]["total_income"] == 300.0


def test_payroll_paid_and_advances_metrics(client, staff):
    entry = create_finalized_entry()
    create_payment(entry, amount="300.00", payment_date=TODAY)
    create_advance(create_tailor(), amount="500.00", advance_date=TODAY)

    data = _summary(client, staff).json()["financial"]
    assert data["payroll_paid"] == 300.0
    assert data["salary_advances"] == 500.0
    assert data["expenses"]["total_expenses"] == 0.0


def test_invalid_dates_return_400(client, staff):
    response = _summary(client, staff, date_from="not-a-date")
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "validation_error"


def test_reversed_range_returns_400(client, staff):
    response = _summary(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY - timedelta(days=1)),
    )
    assert response.status_code == 400


def test_database_arithmetic_matches_raw_records(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="1000.00",
        payment_type=CustomerPayment.PaymentType.FINAL,
    )
    _payment(
        invoice=invoice,
        amount="300.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )
    create_expense(amount="100.00", expense_date=TODAY)

    gross = sum(
        (
            row.amount
            for row in CustomerPayment.objects.exclude(
                payment_type=CustomerPayment.PaymentType.REFUND
            )
        ),
        Decimal("0.00"),
    )
    refunds = sum(
        (
            row.amount
            for row in CustomerPayment.objects.filter(
                payment_type=CustomerPayment.PaymentType.REFUND
            )
        ),
        Decimal("0.00"),
    )
    expense_total = sum((row.amount for row in Expense.objects.all()), Decimal("0.00"))

    report = build_reports_summary()
    assert report["financial"]["income"]["total_income"] == float(gross - refunds)
    assert report["financial"]["expenses"]["total_expenses"] == float(expense_total)
    assert report["financial"]["net_position"] == float(gross - refunds - expense_total)
