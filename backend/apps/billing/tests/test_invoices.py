"""Invoice API tests: RBAC, creation rules, snapshots, filters and history."""

from datetime import date, timedelta

import pytest
from django.db import IntegrityError

from apps.billing.models import Invoice
from apps.billing.tests.helpers import (
    available_orders_url,
    create_invoice,
    create_order,
    invoice_detail_url,
    invoice_list_url,
    invoice_payments_url,
    make_owner,
    make_staff,
    order_invoice_url,
)
from apps.customers.tests.helpers import auth_header

pytestmark = pytest.mark.django_db

TODAY = date.today()


def create_customer_alt():
    from apps.customers.tests.helpers import create_customer

    return create_customer(full_name="Alternate Customer", mobile_number="9000000000")


@pytest.fixture
def owner():
    return make_owner()


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def customer():
    from apps.customers.tests.helpers import create_customer

    return create_customer()


@pytest.fixture
def order(customer):
    return create_order(customer)


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _valid_payload(order, **extra):
    payload = {"order": order.id}
    payload.update(extra)
    return payload


def test_anonymous_denied(client, order):
    assert client.get(invoice_list_url()).status_code == 401
    assert (
        client.post(
            invoice_list_url(),
            _valid_payload(order),
            content_type="application/json",
        ).status_code
        == 401
    )
    invoice = create_invoice(order)
    assert client.get(invoice_detail_url(invoice.id)).status_code == 401
    assert client.get(invoice_payments_url(invoice.id)).status_code == 401


def test_owner_can_read_invoices(client, owner, order):
    invoice = create_invoice(order)
    response = client.get(invoice_list_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = client.get(invoice_detail_url(invoice.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["invoice_number"] == invoice.invoice_number


def test_owner_cannot_create_invoice(client, owner, order):
    response = client.post(
        invoice_list_url(),
        _valid_payload(order),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_staff_can_create_invoice(client, staff, order):
    response = client.post(
        invoice_list_url(),
        _valid_payload(order),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["invoice_number"].startswith("INV-")
    assert data["order"]["id"] == order.id
    assert data["customer"]["id"] == order.customer_id
    assert data["status"] == Invoice.Status.UNPAID
    assert data["amount_paid"] == 0.0
    assert data["balance_due"] == 450.5
    assert data["payment_count"] == 0
    assert data["created_by_name"] == staff.username


def test_invalid_order_rejected(client, staff):
    response = client.post(
        invoice_list_url(),
        {"order": 999999},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_duplicate_invoice_rejected(client, staff, order):
    create_invoice(order)
    response = client.post(
        invoice_list_url(),
        _valid_payload(order),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "This order already has an invoice."


def test_duplicate_invoice_rejected_on_convenience_endpoint(client, staff, order):
    create_invoice(order)
    response = client.post(
        order_invoice_url(order.id), {}, content_type="application/json", **_auth(staff)
    )
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "This order already has an invoice."


def test_anonymous_cannot_list_available_orders(client):
    assert client.get(available_orders_url()).status_code == 401


def test_available_orders_requires_authentication_roles(client, staff, owner, order):
    response = client.get(available_orders_url(), **_auth(staff))
    assert response.status_code == 200
    response = client.get(available_orders_url(), **_auth(owner))
    assert response.status_code == 200


def test_order_without_invoice_is_available(client, staff, order):
    response = client.get(available_orders_url(), **_auth(staff))
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    result = body["results"][0]
    assert result["id"] == order.id
    assert result["order_number"] == order.order_number
    assert result["customer"]["full_name"] == order.customer.full_name
    assert result["total_amount"] == 450.5


def test_invoiced_order_is_not_available(client, staff, order):
    create_invoice(order)
    response = client.get(available_orders_url(), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_available_orders_excludes_every_invoiced_order(client, staff, order):
    create_invoice(order)
    invoiced_other_order = create_order(create_customer_alt())
    create_invoice(invoiced_other_order)
    eligible = create_order(create_customer_alt())

    response = client.get(available_orders_url(), **_auth(staff))
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["id"] == eligible.id
    assert invoiced_other_order.id not in [r["id"] for r in body["results"]]


def test_created_invoice_makes_order_disappear_from_available(client, staff, order):
    response = client.get(available_orders_url(), **_auth(staff))
    assert response.json()["count"] == 1

    response = client.post(
        invoice_list_url(),
        _valid_payload(order),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201

    response = client.get(available_orders_url(), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_available_orders_search_filter(client, staff, customer):
    first = create_order(customer)
    second = create_order(create_customer_alt())

    response = client.get(
        available_orders_url(), {"search": first.order_number}, **_auth(staff)
    )
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["id"] == first.id

    response = client.get(
        available_orders_url(), {"search": second.customer.full_name}, **_auth(staff)
    )
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["id"] == second.id

    response = client.get(
        available_orders_url(), {"search": "NO-MATCH-xyz"}, **_auth(staff)
    )
    assert response.json()["count"] == 0


def test_available_orders_paginated(client, staff):
    for _ in range(25):
        create_order()
    response = client.get(available_orders_url(), **_auth(staff))
    body = response.json()
    assert body["count"] == 25
    assert len(body["results"]) == 20
    assert body["next"] is not None


def test_created_by_comes_from_authenticated_user(client, staff, owner, order):
    response = client.post(
        invoice_list_url(),
        _valid_payload(order),
        content_type="application/json",
        **_auth(staff),
    )
    invoice = Invoice.objects.get(pk=response.json()["id"])
    assert invoice.created_by_id == staff.id

    second_order = create_order(create_customer_alt())
    response = client.post(
        invoice_list_url(),
        _valid_payload(second_order),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_client_cannot_override_created_by(client, staff, order):
    other = make_staff(username="other_staff")
    response = client.post(
        invoice_list_url(),
        _valid_payload(order, created_by=other.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    invoice = Invoice.objects.get(pk=response.json()["id"])
    assert invoice.created_by_id == staff.id


def test_invoice_item_snapshots_and_totals(client, staff, order):
    response = client.post(
        invoice_list_url(),
        _valid_payload(order),
        content_type="application/json",
        **_auth(staff),
    )
    data = response.json()
    assert data["subtotal"] == 450.5
    assert data["total_amount"] == 450.5
    assert len(data["items"]) == 2

    shirt = next(item for item in data["items"] if item["garment_code"] == "SHIRT")
    pant = next(item for item in data["items"] if item["garment_code"] == "PANT")
    assert shirt["garment_type"] == "Shirt"
    assert shirt["quantity"] == 2
    assert shirt["unit_price"] == 100.0
    assert shirt["line_total"] == 200.0
    assert pant["garment_type"] == "Pant"
    assert pant["quantity"] == 1
    assert pant["unit_price"] == 250.5
    assert pant["line_total"] == 250.5


def test_invoice_number_unique_constraint(order):
    from apps.billing.models import Invoice

    first = create_invoice(order)
    second_order = create_order(create_customer_alt())
    second = create_invoice(second_order)
    assert first.invoice_number != second.invoice_number

    with pytest.raises(IntegrityError):
        Invoice.objects.create(
            order=second_order,
            invoice_number=first.invoice_number,
            invoice_date=TODAY,
            subtotal=0,
            total_amount=0,
        )


def test_invoice_unchanged_after_order_changes(client, staff, order):
    response = client.post(
        invoice_list_url(),
        _valid_payload(order),
        content_type="application/json",
        **_auth(staff),
    )
    invoice_id = response.json()["id"]
    original_items = response.json()["items"]

    shirt = order.items.get(garment_type="SHIRT")
    shirt.quantity = 5
    shirt.unit_price = 999.99
    shirt.save()
    order.total_amount = 999.99 * 5 + 250.50
    order.save(update_fields=["total_amount"])

    response = client.get(invoice_detail_url(invoice_id), **_auth(staff))
    data = response.json()
    assert data["subtotal"] == 450.5
    assert data["total_amount"] == 450.5
    assert data["items"] == original_items


def test_convenience_order_invoice_endpoint(client, staff, order):
    response = client.post(
        order_invoice_url(order.id), {}, content_type="application/json", **_auth(staff)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["invoice"]["order"]["id"] == order.id
    assert body["invoice"]["invoice_number"].startswith("INV-")

    duplicate = client.post(
        order_invoice_url(order.id), {}, content_type="application/json", **_auth(staff)
    )
    assert duplicate.status_code == 400

    assert Invoice.objects.filter(order=order).count() == 1


def test_owner_cannot_use_convenience_endpoint(client, owner, order):
    response = client.post(
        order_invoice_url(order.id), {}, content_type="application/json", **_auth(owner)
    )
    assert response.status_code == 403


def test_invoice_no_physical_delete_and_no_update(client, staff, order):
    invoice = create_invoice(order)
    invoice_id = invoice.id

    assert (
        client.delete(invoice_detail_url(invoice_id), **_auth(staff)).status_code == 405
    )
    assert (
        client.patch(
            invoice_detail_url(invoice_id), {"notes": "x"}, **_auth(staff)
        ).status_code
        == 405
    )
    assert (
        client.put(
            invoice_detail_url(invoice_id), {"notes": "x"}, **_auth(staff)
        ).status_code
        == 405
    )
    assert Invoice.objects.filter(pk=invoice_id).exists()


def test_invoice_search_filter(client, staff, order, customer):
    invoice = create_invoice(order)

    response = client.get(
        invoice_list_url(), {"search": invoice.invoice_number}, **_auth(staff)
    )
    assert response.json()["count"] == 1

    response = client.get(
        invoice_list_url(), {"search": order.order_number}, **_auth(staff)
    )
    assert response.json()["count"] == 1

    response = client.get(
        invoice_list_url(), {"search": customer.full_name}, **_auth(staff)
    )
    assert response.json()["count"] == 1

    response = client.get(
        invoice_list_url(), {"search": "NO-MATCH-xyz"}, **_auth(staff)
    )
    assert response.json()["count"] == 0


def test_invoice_customer_and_order_filters(client, staff, order, customer):
    create_invoice(order)
    other = create_customer_alt()
    other_order = create_order(other)
    other_invoice = create_invoice(other_order)

    response = client.get(invoice_list_url(), {"customer": customer.id}, **_auth(staff))
    assert response.json()["count"] == 1

    response = client.get(invoice_list_url(), {"order": other_order.id}, **_auth(staff))
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == other_invoice.id


def test_invoice_date_filters_inclusive(client, staff):
    first = create_invoice(create_order(), invoice_date=TODAY - timedelta(days=3))
    second = create_invoice(create_order(create_customer_alt()), invoice_date=TODAY)

    response = client.get(
        invoice_list_url(),
        {
            "date_from": str(TODAY - timedelta(days=3)),
            "date_to": str(TODAY),
        },
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 2

    response = client.get(
        invoice_list_url(),
        {"date_from": str(TODAY - timedelta(days=1))},
        **_auth(staff),
    )
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == second.id

    response = client.get(
        invoice_list_url(), {"date_to": str(TODAY - timedelta(days=2))}, **_auth(staff)
    )
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == first.id


def test_invoice_reversed_and_invalid_dates_rejected(client, staff):
    response = client.get(
        invoice_list_url(),
        {"date_from": str(TODAY), "date_to": str(TODAY - timedelta(days=1))},
        **_auth(staff),
    )
    assert response.status_code == 400

    response = client.get(
        invoice_list_url(), {"date_from": "not-a-date"}, **_auth(staff)
    )
    assert response.status_code == 400


def test_invoice_status_filters(client, staff):
    unpaid = create_invoice(create_order())
    partial_order = create_order(create_customer_alt())
    partial = create_invoice(partial_order)
    from apps.billing.tests.helpers import create_payment

    create_payment(partial, amount="200.00")
    paid_order = create_order(create_customer_alt())
    paid = create_invoice(paid_order)
    create_payment(paid, amount="450.50")

    response = client.get(invoice_list_url(), {"status": "UNPAID"}, **_auth(staff))
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == unpaid.id

    response = client.get(
        invoice_list_url(), {"status": "PARTIALLY_PAID"}, **_auth(staff)
    )
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == partial.id

    response = client.get(invoice_list_url(), {"status": "PAID"}, **_auth(staff))
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == paid.id

    response = client.get(invoice_list_url(), {"status": "BOGUS"}, **_auth(staff))
    assert response.status_code == 400


def test_invoice_pagination(client, staff):
    for index in range(25):
        create_invoice(create_order())
    response = client.get(invoice_list_url(), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["count"] == 25
    assert len(response.json()["results"]) == 6
    assert response.json()["next"] is not None


def test_invoice_status_derived_not_stored(client, staff, order):
    invoice = create_invoice(order)
    assert not hasattr(invoice, "status") or getattr(invoice, "status", None) is None
    from apps.billing.tests.helpers import create_payment

    create_payment(invoice, amount="450.50")
    response = client.get(invoice_detail_url(invoice.id), **_auth(staff))
    assert response.json()["status"] == "PAID"
