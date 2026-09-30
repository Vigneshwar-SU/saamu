"""Internal customer notes on staff-facing surfaces.

``Customer.notes`` is free-form internal working data ("Testing phase",
"created by integration check"). Staff need it next to the name so they can
tell two customers with the same name apart, and so the label reads
``Name (Notes)``.

The hard rule this module protects: notes are **internal only**. They may
appear on staff screens, and must never reach the customer - neither in the
printed bill nor in a WhatsApp / reminder message.
"""

import pytest
from decimal import Decimal

from django.utils import timezone

from apps.orders.models import Order, OrderItem, GarmentType
from apps.tailors.tests.helpers import (
    create_customer,
    create_piece_rate,
    create_tailor,
    create_order_with_items,
    get_order_item,
    assign_payload,
    work_assignments_url,
)
from apps.customers.tests.helpers import auth_header, make_staff

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def test_customer_detail_exposes_notes(client, staff):
    customer = create_customer(notes="Testing phase")

    response = client.get(f"/api/v1/customers/{customer.id}/", **_auth(staff))

    assert response.status_code == 200
    assert response.json()["notes"] == "Testing phase"


def test_notes_default_to_empty_string(client, staff):
    """A customer with no note must not surface a null the UI has to handle."""
    customer = create_customer(notes="")

    response = client.get(f"/api/v1/customers/{customer.id}/", **_auth(staff))

    assert response.json()["notes"] == ""


def test_nested_customer_in_order_exposes_notes(client, staff):
    """Orders embed the customer, so the note must ride along there too."""
    customer = create_customer(notes="Prefers morning pickup")
    create_order_with_items(customer, {"SHIRT": 1})

    response = client.get("/api/v1/orders/", **_auth(staff))

    assert response.status_code == 200
    assert response.json()["results"][0]["customer"]["notes"] == "Prefers morning pickup"


def test_nested_customer_in_invoice_exposes_notes(client, staff):
    customer = create_customer(notes="Prefers evening delivery")
    order = Order.objects.create(customer=customer)
    OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        quantity=1,
        unit_price=Decimal("100.00"),
    )

    created = client.post(
        f"/api/v1/orders/{order.id}/invoice/",
        {},
        content_type="application/json",
        **_auth(staff),
    )
    assert created.status_code == 201, created.content

    detail = client.get(
        f"/api/v1/invoices/{created.json()['invoice']['id']}/", **_auth(staff)
    )
    assert detail.json()["customer"]["notes"] == "Prefers evening delivery"


def test_work_assignment_exposes_customer_notes(client, staff):
    customer = create_customer(notes="Call before delivery")
    order = create_order_with_items(customer, {"SHIRT": 2})
    item = get_order_item(order, "SHIRT")
    create_piece_rate(garment_type="SHIRT_FULL", rate_per_piece="150.00")

    response = client.post(
        work_assignments_url(),
        assign_payload(create_tailor(), order, item, assigned_quantity=1),
        content_type="application/json",
        **_auth(staff),
    )

    assert response.status_code == 201, response.content
    assert response.json()["order_item"]["customer_notes"] == "Call before delivery"


def test_reminder_candidate_exposes_customer_notes(client, staff):
    customer = create_customer(notes="Testing phase")
    Order.objects.create(customer=customer, status="READY")

    response = client.get("/api/v1/reminders/", **_auth(staff))
    assert response.status_code == 200

    payload = next(
        c
        for c in response.json()["data"]["results"]
        if c["customer"]["id"] == customer.id
    )
    assert payload["customer"]["notes"] == "Testing phase"


def test_manual_reminder_exposes_customer_notes(client, staff):
    from apps.billing.models import ManualReminder

    customer = create_customer(notes="Prefers WhatsApp")
    reminder = ManualReminder.objects.create(
        title="Call back",
        reminder_date=timezone.localdate(),
        customer=customer,
        order=Order.objects.create(customer=customer),
    )

    response = client.get(f"/api/v1/reminders/manual/{reminder.id}/", **_auth(staff))

    assert response.status_code == 200
    assert response.json()["customer"]["notes"] == "Prefers WhatsApp"


def test_income_exposes_customer_notes(client, staff):
    from apps.billing.models import CustomerPayment, Invoice

    customer = create_customer(notes="created by integration check")
    order = Order.objects.create(customer=customer)
    invoice = Invoice.objects.create(order=order)
    payment = CustomerPayment.objects.create(
        invoice=invoice,
        amount=Decimal("500.00"),
        payment_date=timezone.localdate(),
        payment_type=CustomerPayment.PaymentType.ADVANCE,
        payment_method=CustomerPayment.Method.CASH,
    )

    response = client.get("/api/v1/income/", **_auth(staff))

    assert response.status_code == 200
    row = next(r for r in response.json()["results"] if r["id"] == payment.id)
    assert row["customer_notes"] == "created by integration check"


# ---------------------------------------------------------------------------
# Notes must never reach the customer
# ---------------------------------------------------------------------------


def test_printed_bill_omits_internal_notes(client, staff):
    """The printed bill is customer-facing, so notes must stay off it."""
    customer = create_customer(notes="created by integration check")
    order = Order.objects.create(customer=customer)
    OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        quantity=1,
        unit_price=Decimal("100.00"),
    )
    created = client.post(
        f"/api/v1/orders/{order.id}/invoice/",
        {},
        content_type="application/json",
        **_auth(staff),
    )
    invoice_id = created.json()["invoice"]["id"]

    bill = client.get(f"/api/v1/invoices/{invoice_id}/bill/", **_auth(staff))

    assert bill.status_code == 200
    bill_data = bill.json()["bill"]
    assert bill_data["customer"]["full_name"] == customer.full_name
    # Every field the bill actually renders must be free of the internal note.
    assert "created by integration check" not in str(bill_data)


def test_reminder_message_omits_internal_notes(client, staff):
    """The WhatsApp message is the highest-risk leak; assert it explicitly."""
    customer = create_customer(notes="created by integration check")
    Order.objects.create(customer=customer, status="READY")

    response = client.get("/api/v1/reminders/", **_auth(staff))
    payload = next(
        c
        for c in response.json()["data"]["results"]
        if c["customer"]["id"] == customer.id
    )

    assert payload["message"]
    assert "created by integration check" not in payload["message"]


def test_communication_message_omits_internal_notes(client, staff):
    """The order communication composer is also customer-facing.

    A READY order is the one case the backend authors a message for, so that
    is the payload worth asserting against.
    """
    customer = create_customer(notes="created by integration check")
    order = Order.objects.create(customer=customer, status="READY")
    OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        quantity=1,
        unit_price=Decimal("100.00"),
    )

    response = client.get(
        f"/api/v1/communications/messages/prepare/order/{order.id}/", **_auth(staff)
    )

    assert response.status_code == 200, response.content
    body = response.json()["data"]
    assert body["message"]
    assert "created by integration check" not in str(body)
