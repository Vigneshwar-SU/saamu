"""Customer payment API tests: RBAC, validation, derived status, filters and
concurrency safety."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.billing.models import CustomerPayment, Invoice
from apps.billing.services import invoice_summary
from apps.billing.tests.helpers import (
    create_invoice,
    create_order,
    create_payment,
    invoice_detail_url,
    invoice_payments_url,
    make_owner,
    make_staff,
)
from apps.customers.tests.helpers import auth_header

pytestmark = pytest.mark.django_db

TODAY = date.today()


@pytest.fixture
def owner():
    return make_owner()


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


def test_anonymous_denied(client, invoice):
    assert client.get(invoice_payments_url(invoice.id)).status_code == 401
    assert (
        client.post(
            invoice_payments_url(invoice.id),
            _valid_payload(),
            content_type="application/json",
        ).status_code
        == 401
    )


def test_owner_can_read_payment_history(client, owner, invoice):
    create_payment(invoice, amount="100.00")
    response = client.get(invoice_payments_url(invoice.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 1
    payment = response.json()["results"][0]
    assert payment["amount"] == 100.0
    assert payment["payment_method_display"] == "Cash"
    assert payment["invoice_number"] == invoice.invoice_number


def test_owner_cannot_record_payment(client, owner, invoice):
    response = client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 0


def test_staff_can_record_payment(client, staff, invoice):
    response = client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["payment"]["amount"] == 100.0
    assert body["payment"]["recorded_by_name"] == staff.username
    assert body["invoice"]["status"] == Invoice.Status.PARTIALLY_PAID
    assert body["invoice"]["amount_paid"] == 100.0
    assert body["invoice"]["balance_due"] == 350.5


def test_zero_and_negative_payments_rejected(client, staff, invoice):
    for amount in ("0", "0.00", "-1", "-100.00"):
        response = client.post(
            invoice_payments_url(invoice.id),
            _valid_payload(amount=amount),
            content_type="application/json",
            **_auth(staff),
        )
        assert response.status_code == 400, amount
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 0


def test_overpayment_rejected(client, staff, invoice):
    response = client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(amount="500.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    body = response.json()
    assert "cannot exceed" in body["error"]["message"]
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 0


def test_exact_final_payment_produces_paid(client, staff, invoice):
    response = client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(amount="450.50"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["invoice"]["status"] == "PAID"
    assert response.json()["invoice"]["balance_due"] == 0.0
    assert response.json()["invoice"]["payment_count"] == 1


def test_multiple_partial_payments_produce_partially_paid(client, staff, invoice):
    client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(amount="100.00"),
        content_type="application/json",
        **_auth(staff),
    )
    client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(amount="200.00"),
        content_type="application/json",
        **_auth(staff),
    )
    response = client.get(invoice_detail_url(invoice.id), **_auth(staff))
    data = response.json()
    assert data["status"] == "PARTIALLY_PAID"
    assert data["amount_paid"] == 300.0
    assert data["balance_due"] == 150.5
    assert data["payment_count"] == 2


def test_no_payment_produces_unpaid(client, staff, invoice):
    response = client.get(invoice_detail_url(invoice.id), **_auth(staff))
    assert response.json()["status"] == "UNPAID"
    assert response.json()["amount_paid"] == 0.0


def test_recorded_by_server_authoritative(client, staff, invoice):
    other = make_staff(username="other_staff")
    response = client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(recorded_by=other.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    payment = CustomerPayment.objects.get(pk=response.json()["payment"]["id"])
    assert payment.recorded_by_id == staff.id


def test_payment_method_validation(client, staff, invoice):
    response = client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(payment_method="CHEQUE"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400

    response = client.post(
        invoice_payments_url(invoice.id),
        _valid_payload(payment_method="UPI"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201


def test_payment_history_append_only(client, staff, invoice):
    payment = create_payment(invoice, amount="50.00")
    payment_id = payment.id
    url = invoice_payments_url(invoice.id)
    payment_url = f"/api/v1/invoices/{invoice.id}/payments/{payment.id}/"

    # No update/delete endpoint exists for a single payment: PUT, PATCH and
    # DELETE on a payment detail route are not routed (404).
    for method in ("put", "patch", "delete"):
        response = getattr(client, method)(payment_url, **_auth(staff))
        assert response.status_code == 404, method

    assert CustomerPayment.objects.filter(pk=payment_id).exists()
    assert client.get(url, **_auth(staff)).json()["count"] == 1


def test_payment_filters(client, staff, invoice):
    create_payment(
        invoice,
        amount="100.00",
        payment_date=TODAY,
        method=CustomerPayment.Method.CASH,
    )
    create_payment(
        invoice,
        amount="200.00",
        payment_date=TODAY - timedelta(days=4),
        method=CustomerPayment.Method.UPI,
    )

    response = client.get(
        invoice_payments_url(invoice.id),
        {"payment_method": "CASH"},
        **_auth(staff),
    )
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["amount"] == 100.0

    response = client.get(
        invoice_payments_url(invoice.id),
        {
            "date_from": str(TODAY - timedelta(days=1)),
            "date_to": str(TODAY),
        },
        **_auth(staff),
    )
    assert response.json()["count"] == 1

    response = client.get(
        invoice_payments_url(invoice.id), {"payment_method": "BOGUS"}, **_auth(staff)
    )
    assert response.status_code == 400

    response = client.get(
        invoice_payments_url(invoice.id),
        {"date_from": "not-a-date"},
        **_auth(staff),
    )
    assert response.status_code == 400


def test_payment_pagination(client, staff, invoice):
    for index in range(25):
        create_payment(
            invoice,
            amount=f"{index + 1}.00",
            payment_date=TODAY - timedelta(days=index),
        )
    response = client.get(invoice_payments_url(invoice.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 25
    assert len(response.json()["results"]) == 20
    assert response.json()["next"] is not None


@pytest.mark.django_db(transaction=True)
def test_concurrent_payments_cannot_overpay():
    from threading import Thread

    from django.db import connections
    from rest_framework.exceptions import ValidationError

    from apps.billing.services import record_customer_payment

    invoice = create_invoice(create_order())
    staff = make_staff()
    assert invoice_summary(invoice)["balance_due"] == Decimal("450.50")

    errors = []

    def record(amount):
        try:
            record_customer_payment(
                invoice=invoice,
                amount=amount,
                payment_method=CustomerPayment.Method.CASH,
                recorded_by=staff,
            )
        except ValidationError as exc:
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [Thread(target=record, args=(Decimal("300.00"),)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(errors) == 1
    assert CustomerPayment.objects.filter(invoice=invoice).count() == 1
    assert invoice_summary(invoice)["amount_paid"] == Decimal("300.00")
    assert invoice_summary(invoice)["balance_due"] == Decimal("150.50")
