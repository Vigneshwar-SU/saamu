"""Customer-derived income API tests: RBAC, read-only, filters and history.

Phase 13 derives income from the append-only customer payments instead of
manual ledger entries: each payment contributes to income exactly once and
REFUND transactions reduce net income. The income endpoint is strictly
read-only - payments are only ever recorded through the billing API.
"""

from datetime import date, timedelta

import pytest

from apps.authentication.tests.helpers import auth_header
from apps.billing.models import CustomerPayment
from apps.billing.tests.helpers import create_invoice, create_payment
from apps.finance.tests.helpers import (
    income_detail_url,
    income_list_url,
    income_summary_url,
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


def _payment(invoice=None, amount="500.00", payment_date=None, **extra):
    return create_payment(
        invoice or create_invoice(),
        amount=amount,
        payment_date=payment_date or TODAY,
        **extra,
    )


def test_anonymous_denied(client):
    assert client.get(income_list_url()).status_code == 401
    assert client.get(income_summary_url()).status_code == 401
    assert (
        client.post(income_list_url(), {}, content_type="application/json").status_code
        == 401
    )


def test_owner_and_staff_can_read_income_list(client, owner, staff):
    _payment(amount="500.00")
    _payment(amount="250.00", payment_type=CustomerPayment.PaymentType.PARTIAL)

    for user in (owner, staff):
        response = client.get(income_list_url(), **_auth(user))
        assert response.status_code == 200
        assert response.json()["count"] == 2


def test_income_list_shows_payment_details(client, staff):
    payment = _payment(
        amount="500.00",
        payment_type=CustomerPayment.PaymentType.ADVANCE,
        method=CustomerPayment.Method.UPI,
        reference="PAY-REF-1",
    )

    response = client.get(income_list_url(), **_auth(staff))
    data = response.json()["results"][0]
    assert data["id"] == payment.id
    assert data["payment_type"] == CustomerPayment.PaymentType.ADVANCE
    assert data["payment_type_display"] == "Advance"
    assert data["payment_method"] == CustomerPayment.Method.UPI
    assert data["payment_method_display"] == "UPI"
    assert data["amount"] == 500.0
    assert data["net_amount"] == 500.0
    assert data["invoice_id"] == payment.invoice_id
    assert data["invoice_number"] == payment.invoice.invoice_number
    assert data["order_id"] == payment.invoice.order_id
    assert data["order_number"] == payment.invoice.order.order_number
    assert data["customer_id"] == payment.invoice.order.customer_id
    assert data["customer_name"] == payment.invoice.order.customer.full_name
    assert data["reference"] == "PAY-REF-1"


def test_income_detail_returns_payment(client, owner):
    payment = _payment(amount="500.00")

    response = client.get(income_detail_url(payment.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["amount"] == 500.0


def test_refund_is_shown_as_refund_with_negative_net_amount(client, staff):
    invoice = create_invoice()
    _payment(
        invoice=invoice,
        amount="1000.00",
        payment_type=CustomerPayment.PaymentType.FINAL,
    )
    refund = _payment(
        invoice=invoice,
        amount="300.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    response = client.get(income_list_url(), **_auth(staff))
    results = response.json()["results"]
    assert response.json()["count"] == 2

    refund_row = next(row for row in results if row["id"] == refund.id)
    assert refund_row["payment_type"] == CustomerPayment.PaymentType.REFUND
    assert refund_row["payment_type_display"] == "Refund"
    assert refund_row["amount"] == 300.0
    assert refund_row["net_amount"] == -300.0


def test_income_endpoint_is_read_only(client, staff):
    payment = _payment(amount="500.00")

    payload = {"amount": "100.00"}
    assert (
        client.post(
            income_list_url(), payload, content_type="application/json", **_auth(staff)
        ).status_code
        == 405
    )
    assert (
        client.put(
            income_detail_url(payment.id),
            payload,
            content_type="application/json",
            **_auth(staff),
        ).status_code
        == 405
    )
    assert (
        client.patch(
            income_detail_url(payment.id),
            payload,
            content_type="application/json",
            **_auth(staff),
        ).status_code
        == 405
    )
    assert (
        client.delete(income_detail_url(payment.id), **_auth(staff)).status_code == 405
    )


def test_income_read_never_mutates_payments(client, staff):
    invoice = create_invoice()
    payment = _payment(invoice=invoice, amount="500.00")
    _payment(
        invoice=invoice,
        amount="300.00",
        payment_type=CustomerPayment.PaymentType.REFUND,
    )

    client.get(income_list_url(), **_auth(staff))

    assert CustomerPayment.objects.filter(invoice=invoice).count() == 2
    assert CustomerPayment.objects.get(pk=payment.id).amount == 500.0


def test_income_date_range_filter(client, staff):
    _payment(amount="100.00", payment_date=TODAY)
    _payment(amount="200.00", payment_date=TODAY + timedelta(days=3))
    _payment(amount="300.00", payment_date=TODAY - timedelta(days=3))

    response = client.get(
        income_list_url(),
        {
            "date_from": str(TODAY - timedelta(days=1)),
            "date_to": str(TODAY + timedelta(days=2)),
        },
        **_auth(staff),
    )
    assert response.json()["count"] == 1


def test_income_inclusive_date_boundaries(client, staff):
    _payment(amount="100.00", payment_date=TODAY)
    _payment(amount="200.00", payment_date=TODAY + timedelta(days=2))

    response = client.get(
        income_list_url(),
        {"date_from": str(TODAY), "date_to": str(TODAY + timedelta(days=2))},
        **_auth(staff),
    )
    assert response.json()["count"] == 2


def test_income_payment_method_filter(client, staff):
    _payment(amount="100.00", method=CustomerPayment.Method.CASH)
    _payment(amount="200.00", method=CustomerPayment.Method.UPI)

    response = client.get(income_list_url(), {"payment_method": "UPI"}, **_auth(staff))
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["payment_method"] == CustomerPayment.Method.UPI

    response = client.get(
        income_list_url(), {"payment_method": "BOGUS"}, **_auth(staff)
    )
    assert response.status_code == 400


def test_income_payment_type_filter(client, staff):
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

    response = client.get(income_list_url(), {"payment_type": "REFUND"}, **_auth(staff))
    assert response.json()["count"] == 1
    assert (
        response.json()["results"][0]["payment_type"]
        == CustomerPayment.PaymentType.REFUND
    )

    response = client.get(income_list_url(), {"payment_type": "BOGUS"}, **_auth(staff))
    assert response.status_code == 400


def test_income_combined_filters(client, staff):
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

    response = client.get(
        income_list_url(),
        {
            "date_from": str(TODAY),
            "date_to": str(TODAY),
            "payment_method": "UPI",
            "payment_type": "PARTIAL",
        },
        **_auth(staff),
    )
    assert response.json()["count"] == 1


def test_income_invalid_date_filters_return_400(client, staff):
    response = client.get(
        income_list_url(), {"date_from": "not-a-date"}, **_auth(staff)
    )
    assert response.status_code == 400

    response = client.get(
        income_list_url(),
        {"date_from": str(TODAY), "date_to": str(TODAY - timedelta(days=1))},
        **_auth(staff),
    )
    assert response.status_code == 400


def test_income_pagination(client, staff):
    for index in range(25):
        _payment(amount=f"{index + 1}.00", payment_date=TODAY - timedelta(days=index))

    response = client.get(income_list_url(), **_auth(staff))
    assert response.json()["count"] == 25
    assert len(response.json()["results"]) == 6
    assert response.json()["next"] is not None
