"""Phase 11 customer payment type tests: ADVANCE / PARTIAL / FINAL / REFUND
rules, refund awareness of totals and status, and refund audit links."""

from datetime import date
from decimal import Decimal

import pytest

from apps.billing.models import CustomerPayment, Invoice
from apps.billing.services import invoice_summary
from apps.billing.tests.helpers import (
    create_invoice,
    create_order,
    create_payment,
    invoice_payments_url,
    make_owner,
    make_staff,
)
from apps.customers.tests.helpers import auth_header

pytestmark = pytest.mark.django_db

TODAY = date.today()


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def invoice():
    return create_invoice(create_order())


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _valid_payload(**extra):
    payload = {
        "amount": "100.00",
        "payment_date": str(TODAY),
        "payment_method": CustomerPayment.Method.CASH,
    }
    payload.update(extra)
    return payload


def _record(client, staff, invoice, **extra):
    return client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(**extra),
        content_type="application/json",
        **_auth(staff),
    )


def test_payment_type_returned_in_history(client, staff, invoice):
    response = _record(client, staff, invoice, amount="100.00", payment_type="ADVANCE")
    assert response.status_code == 201
    payment = response.json()["payment"]
    assert payment["payment_type"] == "ADVANCE"
    assert payment["payment_type_display"] == "Advance"

    history = client.get(invoice_payments_url(invoice.id), **_auth(staff)).json()
    assert history["count"] == 1
    assert history["results"][0]["payment_type"] == "ADVANCE"


def test_advance_payment_accepted(client, staff, invoice):
    response = _record(client, staff, invoice, amount="150.00", payment_type="ADVANCE")
    assert response.status_code == 201
    assert response.json()["invoice"]["status"] == "PARTIALLY_PAID"


def test_advance_payment_cannot_overpay(client, staff, invoice):
    response = _record(client, staff, invoice, amount="500.00", payment_type="ADVANCE")
    assert response.status_code == 400
    assert "cannot exceed" in response.json()["error"]["message"]


def test_partial_payment_must_be_less_than_balance(client, staff, invoice):
    response = _record(client, staff, invoice, amount="450.50", payment_type="PARTIAL")
    assert response.status_code == 400
    assert "FINAL" in response.json()["error"]["message"]
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 0


def test_final_payment_must_equal_balance(client, staff, invoice):
    response = _record(client, staff, invoice, amount="400.00", payment_type="FINAL")
    assert response.status_code == 400
    assert "must equal" in response.json()["error"]["message"]
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 0


def test_final_payment_clears_balance(client, staff, invoice):
    response = _record(client, staff, invoice, amount="450.50", payment_type="FINAL")
    assert response.status_code == 201
    body = response.json()
    assert body["invoice"]["status"] == "PAID"
    assert body["invoice"]["balance_due"] == 0.0
    assert body["invoice"]["payment_count"] == 1


def test_final_after_partial(client, staff, invoice):
    _record(client, staff, invoice, amount="100.00", payment_type="PARTIAL")
    response = _record(client, staff, invoice, amount="350.50", payment_type="FINAL")
    assert response.status_code == 201
    assert response.json()["invoice"]["status"] == "PAID"
    assert response.json()["invoice"]["payment_count"] == 2


def test_omitted_type_derives_partial_or_final(client, staff, invoice):
    response = _record(client, staff, invoice, amount="100.00")
    assert response.status_code == 201
    assert response.json()["payment"]["payment_type"] == "PARTIAL"

    response = _record(client, staff, invoice, amount="350.50")
    assert response.status_code == 201
    assert response.json()["payment"]["payment_type"] == "FINAL"


def test_invalid_payment_type_rejected(client, staff, invoice):
    response = _record(client, staff, invoice, payment_type="DISCOUNT")
    assert response.status_code == 400


def test_refund_requires_prior_payment(client, staff, invoice):
    response = _record(client, staff, invoice, amount="50.00", payment_type="REFUND")
    assert response.status_code == 400
    assert "cannot exceed the total paid" in response.json()["error"]["message"]
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 0


def test_refund_reduces_total_paid_and_status(client, staff, invoice):
    _record(client, staff, invoice, amount="450.50", payment_type="FINAL")
    response = _record(client, staff, invoice, amount="50.00", payment_type="REFUND")
    assert response.status_code == 201
    body = response.json()
    assert body["invoice"]["status"] == "PARTIALLY_PAID"
    assert body["invoice"]["amount_paid"] == 400.5
    assert body["invoice"]["refunded_amount"] == 50.0
    assert body["invoice"]["gross_paid"] == 450.5
    assert body["invoice"]["balance_due"] == 50.0

    summary = invoice_summary(Invoice.objects.get(pk=invoice.id))
    assert summary["amount_paid"] == Decimal("400.50")
    assert summary["refunded_amount"] == Decimal("50.00")
    assert summary["status"] == Invoice.Status.PARTIALLY_PAID


def test_full_refund_returns_invoice_to_unpaid(client, staff, invoice):
    _record(client, staff, invoice, amount="450.50", payment_type="FINAL")
    response = _record(client, staff, invoice, amount="450.50", payment_type="REFUND")
    assert response.status_code == 201
    assert response.json()["invoice"]["status"] == "UNPAID"
    assert response.json()["invoice"]["amount_paid"] == 0.0
    assert response.json()["invoice"]["balance_due"] == 450.5


def test_refund_cannot_exceed_total_paid(client, staff, invoice):
    _record(client, staff, invoice, amount="100.00", payment_type="PARTIAL")
    response = _record(client, staff, invoice, amount="100.01", payment_type="REFUND")
    assert response.status_code == 400
    assert "cannot exceed the total paid" in response.json()["error"]["message"]
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 1


def test_refund_reference_must_belong_to_invoice(client, staff, invoice):
    other = create_invoice(create_order())
    other_payment = create_payment(other, amount="100.00")
    _record(client, staff, invoice, amount="100.00", payment_type="PARTIAL")
    response = _record(
        client,
        staff,
        invoice,
        amount="10.00",
        payment_type="REFUND",
        refunded_payment=other_payment.id,
    )
    assert response.status_code == 400
    assert "refunded_payment" in response.json()["error"]["details"]
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 1


def test_refund_link_is_auditable(client, staff, invoice):
    first = _record(client, staff, invoice, amount="100.00", payment_type="PARTIAL")
    original_id = first.json()["payment"]["id"]
    response = _record(
        client,
        staff,
        invoice,
        amount="40.00",
        payment_type="REFUND",
        refunded_payment=original_id,
    )
    assert response.status_code == 201
    refund = response.json()["payment"]
    assert refund["refunded_payment"] == original_id

    original = CustomerPayment.objects.get(pk=original_id)
    assert original.payment_type == "PARTIAL"
    assert original.refunds.count() == 1


def test_cannot_refund_a_refund(client, staff, invoice):
    first = _record(client, staff, invoice, amount="100.00", payment_type="PARTIAL")
    refund = _record(
        client,
        staff,
        invoice,
        amount="40.00",
        payment_type="REFUND",
        refunded_payment=first.json()["payment"]["id"],
    )
    response = _record(
        client,
        staff,
        invoice,
        amount="10.00",
        payment_type="REFUND",
        refunded_payment=refund.json()["payment"]["id"],
    )
    assert response.status_code == 400
    assert "another refund" in response.json()["error"]["message"]


def test_refund_respects_other_invoice(client, staff, invoice):
    _record(client, staff, invoice, amount="450.50", payment_type="FINAL")
    _record(client, staff, invoice, amount="100.00", payment_type="REFUND")
    response = _record(client, staff, invoice, amount="400.00", payment_type="REFUND")
    assert response.status_code == 400
    assert "cannot exceed the total paid" in response.json()["error"]["message"]
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 2


def test_status_filter_uses_net_paid(client, staff, invoice):
    _record(client, staff, invoice, amount="450.50", payment_type="FINAL")
    _record(client, staff, invoice, amount="50.00", payment_type="REFUND")

    url = "/api/v1/invoices/?status=PARTIALLY_PAID"
    response = client.get(url, **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == invoice.id

    response = client.get("/api/v1/invoices/?status=PAID", **_auth(staff))
    assert response.json()["count"] == 0


def test_refund_then_refill_returns_to_paid(client, staff, invoice):
    _record(client, staff, invoice, amount="450.50", payment_type="FINAL")
    _record(client, staff, invoice, amount="50.00", payment_type="REFUND")
    response = _record(client, staff, invoice, amount="50.00", payment_type="FINAL")
    assert response.status_code == 201
    assert response.json()["invoice"]["status"] == "PAID"
    assert response.json()["invoice"]["refunded_amount"] == 50.0
    assert response.json()["invoice"]["gross_paid"] == 500.5
