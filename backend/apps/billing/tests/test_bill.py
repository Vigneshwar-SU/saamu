"""Phase 11 digital bill endpoint, ShopDetails singleton and order payment
summary tests."""

from datetime import date
from decimal import Decimal

import pytest

from apps.billing.models import CustomerPayment, ShopDetails
from apps.billing.services import order_payment_summary
from apps.billing.tests.helpers import (
    create_invoice,
    create_order,
    create_payment,
    invoice_bill_url,
    invoice_payments_url,
    make_owner,
    make_staff,
)
from apps.customers.tests.helpers import auth_header
from apps.orders.tests.helpers import order_detail_url

pytestmark = pytest.mark.django_db


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


def _record(client, staff, invoice, amount):
    return client.post(
        invoice_payments_url(invoice.id),
        {
            "amount": amount,
            "payment_date": str(date.today()),
            "payment_method": CustomerPayment.Method.CASH,
        },
        content_type="application/json",
        **_auth(staff),
    )


def test_anonymous_denied(client, invoice):
    assert client.get(invoice_bill_url(invoice.id)).status_code == 401


def test_owner_can_read_bill(client, owner, invoice):
    response = client.get(invoice_bill_url(invoice.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_shop_details_singleton_created_with_defaults(invoice):
    details = ShopDetails.shop_details()
    assert ShopDetails.objects.count() == 1
    assert details.name == "Saamu Tailors"
    assert details.established_year == 1954
    assert ShopDetails.shop_details().pk == details.pk


def test_shop_details_editable_and_used_on_bill(client, owner, invoice):
    details = ShopDetails.shop_details()
    details.name = "Saamu Tailors & Co"
    details.tagline = "Precision tailoring since 1954"
    details.address = "12 Gandhi Market"
    details.phone = "+91 9876543210"
    details.established_year = 1954
    details.save()

    response = client.get(invoice_bill_url(invoice.id), **_auth(owner))
    shop = response.json()["bill"]["shop"]
    assert shop["name"] == "Saamu Tailors & Co"
    assert shop["tagline"] == "Precision tailoring since 1954"
    assert shop["address"] == "12 Gandhi Market"
    assert shop["phone"] == "+91 9876543210"
    assert shop["established_year"] == 1954


def test_bill_contains_customer_order_and_garments(client, owner, invoice):
    response = client.get(invoice_bill_url(invoice.id), **_auth(owner))
    bill = response.json()["bill"]
    customer = invoice.order.customer

    assert bill["customer"]["full_name"] == customer.full_name
    assert bill["customer"]["mobile_number"] == customer.mobile_number
    assert bill["order"]["order_number"] == invoice.order.order_number
    assert bill["order"]["order_date"] == str(invoice.order.order_date)
    assert bill["order"]["status"] == invoice.order.status
    assert len(bill["garments"]) == 2
    first = bill["garments"][0]
    assert first["garment_type"] == "Shirt"
    assert first["garment_code"] == "SHIRT"
    assert first["quantity"] == 2
    assert first["unit_price"] == 100.0
    assert first["line_total"] == 200.0


def test_bill_metadata_and_totals(client, owner, invoice):
    response = client.get(invoice_bill_url(invoice.id), **_auth(owner))
    bill = response.json()["bill"]
    meta = bill["bill_metadata"]
    assert meta["invoice_number"] == invoice.invoice_number
    assert meta["invoice_date"] == str(invoice.invoice_date)
    assert "generated_at" in meta

    totals = bill["totals"]
    assert totals["subtotal"] == 450.5
    assert totals["total_amount"] == 450.5
    assert totals["amount_paid"] == 0.0
    assert totals["balance_due"] == 450.5
    assert totals["status"] == "UNPAID"


def test_bill_reflects_payment_history(client, owner, invoice):
    create_payment(invoice, amount="100.00")
    create_payment(invoice, amount="50.00")
    response = client.get(invoice_bill_url(invoice.id), **_auth(owner))
    bill = response.json()["bill"]
    history = bill["payment_history"]
    assert len(history) == 2
    assert [entry["amount"] for entry in history] == [50.0, 100.0]
    assert history[0]["payment_type"] == "PARTIAL"
    assert bill["totals"]["amount_paid"] == 150.0
    assert bill["totals"]["balance_due"] == 300.5


def test_bill_uses_database_data_not_mock(client, staff, invoice):
    response = client.get(invoice_bill_url(invoice.id), **_auth(staff))
    bill = response.json()["bill"]
    shop = ShopDetails.shop_details()
    assert shop.pk is not None
    assert bill["shop"]["name"] == shop.name


def test_order_payment_summary_without_invoice():
    order = create_order()
    summary = order_payment_summary(order)
    assert summary["has_invoice"] is False
    assert summary["order_total"] == Decimal("450.50")
    assert summary["total_paid"] == Decimal("0.00")
    assert summary["outstanding_balance"] == Decimal("450.50")
    assert summary["payment_status"] == "UNPAID"
    assert summary["refunded_amount"] == Decimal("0.00")


def test_order_payment_summary_reflects_typed_payments():
    invoice = create_invoice(create_order())
    order = invoice.order
    create_payment(
        invoice, amount="450.50", payment_type=CustomerPayment.PaymentType.FINAL
    )
    create_payment(
        invoice, amount="50.00", payment_type=CustomerPayment.PaymentType.REFUND
    )

    summary = order_payment_summary(order)
    assert summary["has_invoice"] is True
    assert summary["order_total"] == Decimal("450.50")
    assert summary["total_paid"] == Decimal("400.50")
    assert summary["outstanding_balance"] == Decimal("50.00")
    assert summary["payment_status"] == "PARTIALLY_PAID"
    assert summary["refunded_amount"] == Decimal("50.00")


def test_order_detail_exposes_payment_summary(client, staff, invoice):
    response = client.get(order_detail_url(invoice.order.id), **_auth(staff))
    assert response.status_code == 200
    summary = response.json()["payment_summary"]
    assert summary is not None
    assert summary["has_invoice"] is True
    assert summary["order_total"] == 450.5
    assert summary["outstanding_balance"] == 450.5
    assert summary["payment_status"] == "UNPAID"
