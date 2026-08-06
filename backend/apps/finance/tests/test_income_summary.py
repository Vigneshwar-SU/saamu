"""Customer-derived income summary tests.

The income summary is the single authoritative aggregation behind both
``GET /api/v1/income/summary/`` and the dashboard. These tests assert the
guardrail that a payment contributes to income exactly once and that refunds
reduce net income, plus filters, RBAC and consistency with raw database data.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.authentication.tests.helpers import auth_header
from apps.billing.models import CustomerPayment
from apps.billing.tests.helpers import create_invoice, create_payment
from apps.finance.services import build_dashboard_summary
from apps.finance.tests.helpers import income_summary_url, make_owner, make_staff

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
    return client.get(income_summary_url(), params, **_auth(user))


def _payment(invoice=None, amount="500.00", payment_date=None, **extra):
    return create_payment(
        invoice or create_invoice(),
        amount=amount,
        payment_date=payment_date or TODAY,
        **extra,
    )


def test_anonymous_denied(client):
    assert client.get(income_summary_url()).status_code == 401


def test_owner_and_staff_can_read_summary(client, owner, staff):
    _payment(amount="500.00")

    for user in (owner, staff):
        response = _summary(client, user)
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_empty_summary_zeros(client, staff):
    data = _summary(client, staff).json()
    assert data["total_income"] == 0.0
    assert data["payment_count"] == 0
    assert data["refund_count"] == 0
    assert data["total_refunds"] == 0.0
    assert data["by_payment_method"] == []
    assert data["by_payment_type"] == []


def test_single_payment_contributes_exactly_once(client, staff):
    _payment(amount="500.00", payment_type=CustomerPayment.PaymentType.ADVANCE)

    data = _summary(client, staff).json()
    assert data["total_income"] == 500.0
    assert data["payment_count"] == 1
    assert data["refund_count"] == 0
    assert data["total_refunds"] == 0.0


def test_multiple_payments_aggregate(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00")
    _payment(invoice=invoice, amount="200.00")
    _payment(invoice=invoice, amount="300.00")

    data = _summary(client, staff).json()
    assert data["total_income"] == 600.0
    assert data["payment_count"] == 3


def test_partial_refund_reduces_net_income(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="1000.00",
        payment_type=CustomerPayment.PaymentType.FINAL,
    )
    _payment(
        invoice=invoice,
        amount="500.00",
        payment_type=CustomerPayment.PaymentType.ADVANCE,
    )
    _payment(
        invoice=invoice,
        amount="300.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    data = _summary(client, staff).json()
    assert data["total_income"] == 1200.0
    assert data["payment_count"] == 2
    assert data["refund_count"] == 1
    assert data["total_refunds"] == 300.0


def test_full_refund_yields_zero_income(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="1000.00",
        payment_type=CustomerPayment.PaymentType.FINAL,
    )
    _payment(
        invoice=invoice,
        amount="1000.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    data = _summary(client, staff).json()
    assert data["total_income"] == 0.0
    assert data["payment_count"] == 1
    assert data["refund_count"] == 1


def test_refund_never_creates_positive_income(client, staff):
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

    data = _summary(client, staff).json()
    assert data["total_income"] == 200.0
    assert data["total_income"] < 500.0


def test_summary_honors_date_range(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00", payment_date=TODAY)
    _payment(invoice=invoice, amount="200.00", payment_date=TODAY + timedelta(days=3))
    _payment(invoice=invoice, amount="300.00", payment_date=TODAY - timedelta(days=3))

    data = _summary(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY + timedelta(days=3)),
    ).json()
    assert data["total_income"] == 300.0
    assert data["payment_count"] == 2


def test_summary_honors_payment_method(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00", method=CustomerPayment.Method.CASH)
    _payment(invoice=invoice, amount="200.00", method=CustomerPayment.Method.UPI)
    _payment(
        invoice=invoice,
        amount="50.00",
        method=CustomerPayment.Method.UPI,
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    data = _summary(client, staff, payment_method="UPI").json()
    assert data["total_income"] == 150.0
    assert data["payment_count"] == 1
    assert data["refund_count"] == 1


def test_summary_honors_payment_type(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="200.00",
        payment_type=CustomerPayment.PaymentType.ADVANCE,
    )
    _payment(
        invoice=invoice,
        amount="250.50",
        payment_type=CustomerPayment.PaymentType.PARTIAL,
    )
    _payment(
        invoice=invoice,
        amount="100.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    data = _summary(client, staff, payment_type="REFUND").json()
    assert data["total_income"] == -100.0
    assert data["payment_count"] == 0
    assert data["refund_count"] == 1

    data = _summary(client, staff, payment_type="ADVANCE").json()
    assert data["total_income"] == 200.0


def test_summary_combined_filters(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="100.00",
        payment_date=TODAY,
        method=CustomerPayment.Method.CASH,
    )
    _payment(
        invoice=invoice,
        amount="200.00",
        payment_date=TODAY,
        method=CustomerPayment.Method.UPI,
        payment_type=CustomerPayment.PaymentType.PARTIAL,
    )
    _payment(
        invoice=invoice,
        amount="50.00",
        payment_date=TODAY - timedelta(days=1),
        method=CustomerPayment.Method.UPI,
    )

    data = _summary(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY),
        payment_method="UPI",
        payment_type="PARTIAL",
    ).json()
    assert data["total_income"] == 200.0
    assert data["payment_count"] == 1


def test_by_payment_type_totals_sum_to_total_income(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="200.00",
        payment_type=CustomerPayment.PaymentType.ADVANCE,
    )
    _payment(
        invoice=invoice, amount="300.00", payment_type=CustomerPayment.PaymentType.FINAL
    )
    _payment(
        invoice=invoice,
        amount="150.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    data = _summary(client, staff).json()
    total_from_rows = sum(row["total"] for row in data["by_payment_type"])
    assert total_from_rows == data["total_income"] == 350.0

    refund_row = next(
        row for row in data["by_payment_type"] if row["payment_type"] == "REFUND"
    )
    assert refund_row["total"] == -150.0


def test_by_payment_method_totals_sum_to_total_income(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00", method=CustomerPayment.Method.CASH)
    _payment(invoice=invoice, amount="300.00", method=CustomerPayment.Method.UPI)
    _payment(
        invoice=invoice,
        amount="50.00",
        method=CustomerPayment.Method.UPI,
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    data = _summary(client, staff).json()
    total_from_rows = sum(row["total"] for row in data["by_payment_method"])
    count_from_rows = sum(row["count"] for row in data["by_payment_method"])
    assert total_from_rows == data["total_income"] == 350.0
    assert count_from_rows == data["payment_count"] == 2


def test_summary_matches_database_aggregation(client, staff):
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

    data = _summary(client, staff).json()
    assert data["total_income"] == float(gross - refunds)


def test_summary_invalid_filters_return_400(client, staff):
    response = _summary(client, staff, payment_method="BOGUS")
    assert response.status_code == 400

    response = _summary(client, staff, payment_type="BOGUS")
    assert response.status_code == 400

    response = _summary(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY - timedelta(days=1)),
    )
    assert response.status_code == 400

    response = _summary(client, staff, date_from="not-a-date")
    assert response.status_code == 400


def test_dashboard_income_equals_income_summary(client, staff):
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

    summary_data = _summary(client, staff).json()
    dashboard = build_dashboard_summary(TODAY, TODAY)
    assert (
        dashboard["financial"]["recorded_income"]
        == summary_data["total_income"]
        == 750.0
    )
