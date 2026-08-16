"""Customer-communication tests.

Phase 18 explicit message-type builders plus the automatic communication
workflow (order status + payment balance select exactly one message). Covers
all five automatic states, authoritative payment values, exact outstanding
balances, zero-balance behaviour, deterministic output, phone normalization,
WhatsApp URL construction and encoding, privacy exclusions, RBAC (anonymous /
OWNER / STAFF), GET-only read-only behaviour, and that preparing a message
never mutates business records.
"""

import urllib.parse
from datetime import date
from decimal import Decimal

import pytest
from rest_framework import status as http_status

from apps.authentication.tests.helpers import auth_header
from apps.billing.communications import (
    MESSAGE_STATE_COLLECTED_PAYMENT_PENDING,
    MESSAGE_STATE_COLLECTED_SETTLED,
    MESSAGE_STATE_LABELS,
    MESSAGE_STATE_ORDER_IN_PROGRESS,
    MESSAGE_STATE_ORDER_RECEIVED,
    MESSAGE_STATE_READY_FOR_COLLECTION,
    MESSAGE_TYPE_ORDER_ACKNOWLEDGEMENT,
    MESSAGE_TYPE_ORDER_STATUS_UPDATE,
    MESSAGE_TYPE_PAYMENT_BALANCE,
    MESSAGE_TYPE_READY_FOR_COLLECTION,
    SUPPORTED_MESSAGE_TYPES,
    build_automatic_order_communication,
    build_order_communication,
    build_whatsapp_url,
    determine_automatic_message_state,
    format_inr,
    normalize_phone,
)
from apps.billing.models import CustomerPayment, Invoice, ShopDetails
from apps.billing.tests.helpers import create_invoice, create_order, create_payment
from apps.customers.models import Customer
from apps.customers.tests.helpers import create_customer, make_owner, make_staff
from apps.orders.models import Order, OrderStatus

pytestmark = pytest.mark.django_db


def prepare_url(order_id):
    return f"/api/v1/communications/messages/prepare/order/{order_id}/"


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


# ---------------------------------------------------------------------------
# Message builder: explicit Phase 18 templates (kept for reminders)
# ---------------------------------------------------------------------------


def test_acknowledgement_template():
    order = create_order()
    payload = build_order_communication(order, MESSAGE_TYPE_ORDER_ACKNOWLEDGEMENT)
    message = payload["message"]
    assert payload["message_type"] == MESSAGE_TYPE_ORDER_ACKNOWLEDGEMENT
    assert "Hello Ravi Kumar," in message
    assert f"Order Number: {order.order_number}" in message
    assert f"Order Date: {order.order_date.strftime('%d %b %Y')}" in message
    assert "Items: 2x Shirt, 1x Pant" in message
    assert "Total: ₹450.50" in message
    assert "Regards," in message
    assert "Saamu Tailors" in message
    # No payment recorded: paid/balance lines are omitted as "not available".
    assert "Amount Paid:" not in message
    assert "Balance:" not in message


def test_acknowledgement_includes_authoritative_paid_and_balance():
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    message = build_order_communication(order, MESSAGE_TYPE_ORDER_ACKNOWLEDGEMENT)[
        "message"
    ]
    assert "Amount Paid: ₹100.00" in message
    assert "Balance: ₹350.50" in message


def test_status_update_template():
    order = create_order(status=OrderStatus.STITCHING)
    message = build_order_communication(order, MESSAGE_TYPE_ORDER_STATUS_UPDATE)[
        "message"
    ]
    assert "Hello Ravi Kumar," in message
    assert "Update on your order." in message
    assert f"Order Number: {order.order_number}" in message
    assert "Current Status: Stitching" in message
    assert "Next Step: Ready." in message
    assert "Regards," in message


def test_status_update_terminal_omits_next_step():
    order = create_order(status=OrderStatus.COLLECTED)
    message = build_order_communication(order, MESSAGE_TYPE_ORDER_STATUS_UPDATE)[
        "message"
    ]
    assert "Current Status: Collected" in message
    assert "Next Step:" not in message


def test_ready_for_collection_template():
    order = create_order(status=OrderStatus.READY)
    message = build_order_communication(order, MESSAGE_TYPE_READY_FOR_COLLECTION)[
        "message"
    ]
    assert "Good news! Your order is ready for collection." in message
    assert f"Order Number: {order.order_number}" in message
    assert "Please collect it from Saamu Tailors." in message
    # Shop address/phone are empty by default and therefore omitted.
    assert "Shop Address:" not in message
    assert "Shop Phone:" not in message
    assert "Regards," in message


def test_payment_balance_template():
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(
        invoice,
        amount="100.00",
        payment_type=CustomerPayment.PaymentType.PARTIAL,
    )
    message = build_order_communication(order, MESSAGE_TYPE_PAYMENT_BALANCE)["message"]
    assert "Payment summary for your order." in message
    assert f"Order Number: {order.order_number}" in message
    assert "Total: ₹450.50" in message
    assert "Amount Paid: ₹100.00" in message
    assert "Balance: ₹350.50" in message
    assert "Payment Status: Partially Paid" in message


# ---------------------------------------------------------------------------
# Automatic message selection: order status + payment balance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "paid", "expected"),
    [
        (OrderStatus.NEW, None, MESSAGE_STATE_ORDER_RECEIVED),
        (OrderStatus.CUTTING, None, MESSAGE_STATE_ORDER_IN_PROGRESS),
        (OrderStatus.STITCHING, None, MESSAGE_STATE_ORDER_IN_PROGRESS),
        (OrderStatus.READY, None, MESSAGE_STATE_READY_FOR_COLLECTION),
        (OrderStatus.READY, "450.50", MESSAGE_STATE_READY_FOR_COLLECTION),
        (OrderStatus.COLLECTED, "450.50", MESSAGE_STATE_COLLECTED_SETTLED),
        (OrderStatus.COLLECTED, "100.00", MESSAGE_STATE_COLLECTED_PAYMENT_PENDING),
    ],
)
def test_state_selection_maps_status_and_balance(status, paid, expected):
    order = create_order(status=status)
    if paid is not None:
        invoice = create_invoice(order=order)
        create_payment(invoice, amount=paid)
    assert determine_automatic_message_state(order) == expected


def test_cancelled_order_has_no_message():
    order = create_order(status=OrderStatus.CANCELLED)
    with pytest.raises(ValueError):
        determine_automatic_message_state(order)
    with pytest.raises(ValueError):
        build_automatic_order_communication(order)


def test_auto_new_order_received_message():
    order = create_order()
    payload = build_automatic_order_communication(order)
    assert payload["message_type"] == MESSAGE_STATE_ORDER_RECEIVED
    assert (
        payload["message_label"] == MESSAGE_STATE_LABELS[MESSAGE_STATE_ORDER_RECEIVED]
    )
    message = payload["message"]
    assert "Hello Ravi Kumar," in message
    assert "Your order has been received." in message
    assert f"Order Number: {order.order_number}" in message
    assert f"Order Date: {order.order_date.strftime('%d %b %Y')}" in message
    assert "Items: 2x Shirt, 1x Pant" in message
    assert "Total: ₹450.50" in message
    assert "Amount Paid: ₹0.00" in message
    assert "Balance: ₹450.50" in message
    assert "Regards," in message
    assert "Saamu Tailors" in message


@pytest.mark.parametrize("status", [OrderStatus.CUTTING, OrderStatus.STITCHING])
def test_auto_in_progress_message(status):
    order = create_order(status=status)
    payload = build_automatic_order_communication(order)
    assert payload["message_type"] == MESSAGE_STATE_ORDER_IN_PROGRESS
    message = payload["message"]
    assert f"Current Status: {OrderStatus(status).label}" in message
    assert "Your order is currently being prepared." in message
    assert "Items: 2x Shirt, 1x Pant" in message
    assert "ready for collection" not in message.lower()


def test_auto_received_fully_paid_message():
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="450.50")
    message = build_automatic_order_communication(order)["message"]
    assert "Amount Paid: ₹450.50" in message
    assert "Payment Status: Fully Paid" in message
    assert "Balance:" not in message


def test_auto_in_progress_fully_paid_message():
    order = create_order(status=OrderStatus.STITCHING)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="450.50")
    message = build_automatic_order_communication(order)["message"]
    assert "Amount Paid: ₹450.50" in message
    assert "Payment Status: Fully Paid" in message
    assert "Balance:" not in message


@pytest.mark.parametrize(
    ("status", "expected_state"),
    [
        (OrderStatus.NEW, MESSAGE_STATE_ORDER_RECEIVED),
        (OrderStatus.STITCHING, MESSAGE_STATE_ORDER_IN_PROGRESS),
        (OrderStatus.READY, MESSAGE_STATE_READY_FOR_COLLECTION),
        (OrderStatus.COLLECTED, MESSAGE_STATE_COLLECTED_SETTLED),
    ],
)
def test_auto_message_label_matches_state(status, expected_state):
    order = create_order(status=status)
    if status == OrderStatus.COLLECTED:
        invoice = create_invoice(order=order)
        create_payment(invoice, amount="450.50")
    payload = build_automatic_order_communication(order)
    assert payload["message_type"] == expected_state
    assert payload["message_label"] == MESSAGE_STATE_LABELS[expected_state]


def test_auto_ready_for_collection_with_balance():
    order = create_order(status=OrderStatus.READY)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    payload = build_automatic_order_communication(order)
    assert payload["message_type"] == MESSAGE_STATE_READY_FOR_COLLECTION
    message = payload["message"]
    assert "Good news! Your order is ready for collection." in message
    assert "Items: 2x Shirt, 1x Pant" in message
    assert "Total: ₹450.50" in message
    assert "Amount Paid: ₹100.00" in message
    assert "Outstanding Balance: ₹350.50" in message
    assert "Please collect your order from Saamu Tailors." in message
    assert "Payment Status: Fully Settled" not in message


def test_auto_ready_for_collection_fully_settled():
    order = create_order(status=OrderStatus.READY)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="450.50")
    message = build_automatic_order_communication(order)["message"]
    assert "Payment Status: Fully Settled" in message
    assert "Outstanding Balance" not in message


def test_auto_ready_includes_shop_location_when_available():
    details = ShopDetails.shop_details()
    details.address = "12, MG Road, Bengaluru"
    details.phone = "080 4123 4567"
    details.save()
    order = create_order(status=OrderStatus.READY)
    message = build_automatic_order_communication(order)["message"]
    assert "Please collect your order from Saamu Tailors." in message
    assert "Shop Address: 12, MG Road, Bengaluru" in message
    assert "Shop Phone: 080 4123 4567" in message


def test_auto_collected_fully_paid_message():
    order = create_order(status=OrderStatus.COLLECTED)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="450.50")
    payload = build_automatic_order_communication(order)
    assert payload["message_type"] == MESSAGE_STATE_COLLECTED_SETTLED
    message = payload["message"]
    assert "Thank you for collecting your order." in message
    assert f"Order Number: {order.order_number}" in message
    assert "Total: ₹450.50" in message
    assert "Amount Paid: ₹450.50" in message
    assert "Payment Status: Fully Settled" in message
    assert "Outstanding Balance" not in message
    assert "Thank you for your business" in message


def test_auto_collected_payment_pending_message():
    order = create_order(status=OrderStatus.COLLECTED)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    payload = build_automatic_order_communication(order)
    assert payload["message_type"] == MESSAGE_STATE_COLLECTED_PAYMENT_PENDING
    message = payload["message"]
    assert "Thank you for collecting your order." in message
    assert "Total: ₹450.50" in message
    assert "Amount Paid: ₹100.00" in message
    assert "Outstanding Balance: ₹350.50" in message
    assert "Please settle the outstanding balance of ₹350.50" in message
    # Collected + outstanding must never claim payment is complete.
    assert "Fully Settled" not in message
    assert "fully paid" not in message.lower()
    assert "payment completed" not in message.lower()


def test_auto_payment_changes_update_message():
    order = create_order()
    invoice = create_invoice(order=order)
    first = build_automatic_order_communication(order)["message"]
    create_payment(invoice, amount="100.00")
    second = build_automatic_order_communication(order)["message"]
    assert first != second
    assert "Amount Paid: ₹0.00" in first
    assert "Amount Paid: ₹100.00" in second
    assert "Balance: ₹350.50" in second


def test_auto_status_change_updates_message():
    order = create_order()
    new_msg = build_automatic_order_communication(order)["message"]
    order.status = OrderStatus.READY
    order.save(update_fields=["status"])
    ready_msg = build_automatic_order_communication(order)["message"]
    assert "Your order has been received." in new_msg
    assert "Good news! Your order is ready for collection." in ready_msg


def test_auto_values_match_payment_summary():
    from apps.billing.services import order_payment_summary

    order = create_order(status=OrderStatus.STITCHING)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="150.00")
    summary = order_payment_summary(order)
    message = build_automatic_order_communication(order)["message"]
    assert f"Total: {format_inr(summary['order_total'])}" in message
    assert f"Amount Paid: {format_inr(summary['total_paid'])}" in message
    assert f"Balance: {format_inr(summary['outstanding_balance'])}" in message


def test_zero_balance_never_shown_as_outstanding_request():
    order = create_order(status=OrderStatus.READY)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="450.50")
    message = build_automatic_order_communication(order)["message"]
    assert "Outstanding Balance: ₹0.00" not in message
    assert "Payment Status: Fully Settled" in message


def test_auto_message_never_mutates_records():
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    counts = (
        Order.objects.count(),
        Invoice.objects.count(),
        CustomerPayment.objects.count(),
        Customer.objects.count(),
    )
    build_automatic_order_communication(order)
    assert (
        Order.objects.count(),
        Invoice.objects.count(),
        CustomerPayment.objects.count(),
        Customer.objects.count(),
    ) == counts


# ---------------------------------------------------------------------------
# Determinism and exact money formatting
# ---------------------------------------------------------------------------


def test_builder_is_deterministic():
    order = create_order()
    first = build_automatic_order_communication(order)
    second = build_automatic_order_communication(order)
    assert first == second


def test_format_inr_exact_grouping():
    assert format_inr(Decimal("450.50")) == "₹450.50"
    assert format_inr(Decimal("45050.50")) == "₹45,050.50"
    assert format_inr(Decimal("1234567.80")) == "₹12,34,567.80"
    assert format_inr(Decimal("100000")) == "₹1,00,000.00"
    assert format_inr(Decimal("0")) == "₹0.00"
    assert format_inr("100.00") == "₹100.00"


# ---------------------------------------------------------------------------
# Missing optional fields
# ---------------------------------------------------------------------------


def test_missing_expected_delivery_omitted():
    order = create_order()
    assert order.expected_delivery_date is None
    received = build_automatic_order_communication(order)["message"]
    order.status = OrderStatus.STITCHING
    order.save(update_fields=["status"])
    in_progress = build_automatic_order_communication(order)["message"]
    assert "Expected Delivery:" not in received
    assert "Expected Delivery:" not in in_progress


def test_expected_delivery_included_when_set():
    order = create_order(expected_delivery_date=date(2026, 8, 20))
    received = build_automatic_order_communication(order)["message"]
    order.status = OrderStatus.STITCHING
    order.save(update_fields=["status"])
    in_progress = build_automatic_order_communication(order)["message"]
    assert "Expected Delivery: 20 Aug 2026" in received
    assert "Expected Delivery: 20 Aug 2026" in in_progress


# ---------------------------------------------------------------------------
# Phone normalization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("9876543210", "919876543210"),
        ("98765 43210", "919876543210"),
        ("09876543210", "919876543210"),
        ("+919876543210", "919876543210"),
        ("+91 98765 43210", "919876543210"),
        ("+91-98765-43210", "919876543210"),
        ("+1 202 555 0123", "12025550123"),
        ("+44 20 7946 0958", "442079460958"),
        ("", None),
        ("   ", None),
        (None, None),
        ("abc123", None),
        ("123", None),
        ("5555555555", None),
        ("12345678901", None),
        ("+1234", None),
        ("+98765", None),
        ("+1 202 555 0123456789", None),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_build_whatsapp_url_rejects_non_digit_destination():
    assert build_whatsapp_url("javascript:alert(1)", "hello") is None
    assert build_whatsapp_url("", "hello") is None
    assert build_whatsapp_url(None, "hello") is None


# ---------------------------------------------------------------------------
# API: response shape, encoding, RBAC, errors, read-only, no mutation
# ---------------------------------------------------------------------------


def test_response_shape(client, staff):
    order = create_order()
    response = client.get(prepare_url(order.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    data = response.data
    assert set(data) == {"success", "data"}
    assert data["success"] is True
    assert set(data["data"]) == {
        "message_type",
        "message_label",
        "message",
        "phone_number",
        "whatsapp_url",
    }


def test_whatsapp_url_encoding(client, staff):
    order = create_order()
    response = client.get(prepare_url(order.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    data = response.data["data"]
    assert data["phone_number"] == "919876543210"
    url = data["whatsapp_url"]
    assert url.startswith("https://wa.me/919876543210?text=")
    assert " " not in url
    assert "\n" not in url
    decoded = urllib.parse.unquote(url.split("?", 1)[1].split("=", 1)[1])
    assert decoded == data["message"]


def test_invalid_phone_yields_no_whatsapp_url(client, staff):
    customer = create_customer(mobile_number="not-a-number")
    order = create_order(customer=customer)
    response = client.get(prepare_url(order.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    data = response.data["data"]
    assert data["message"]
    assert data["phone_number"] is None
    assert data["whatsapp_url"] is None


def test_empty_phone_yields_no_whatsapp_url(client, staff):
    customer = create_customer(mobile_number="")
    order = create_order(customer=customer)
    response = client.get(prepare_url(order.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    data = response.data["data"]
    assert data["message"]
    assert data["phone_number"] is None
    assert data["whatsapp_url"] is None


def test_api_is_deterministic(client, staff):
    order = create_order()
    first = client.get(prepare_url(order.id), **_auth(staff)).data
    second = client.get(prepare_url(order.id), **_auth(staff)).data
    assert first == second


def test_anonymous_gets_401(client):
    order = create_order()
    response = client.get(prepare_url(order.id))
    assert response.status_code == http_status.HTTP_401_UNAUTHORIZED


def test_owner_and_staff_can_prepare(client, owner, staff):
    order = create_order()
    for user in (owner, staff):
        response = client.get(prepare_url(order.id), **_auth(user))
        assert response.status_code == http_status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["message_type"] == MESSAGE_STATE_ORDER_RECEIVED


def test_obsolete_message_type_param_is_ignored(client, staff):
    order = create_order()
    with_type = client.get(
        prepare_url(order.id), {"message_type": "SEND_NOW"}, **_auth(staff)
    )
    without_type = client.get(prepare_url(order.id), **_auth(staff))
    assert with_type.status_code == http_status.HTTP_200_OK
    assert without_type.status_code == http_status.HTTP_200_OK
    assert with_type.data == without_type.data


def test_api_auto_selects_ready_message(client, staff):
    order = create_order(status=OrderStatus.READY)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    response = client.get(prepare_url(order.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    data = response.data["data"]
    assert data["message_type"] == MESSAGE_STATE_READY_FOR_COLLECTION
    assert (
        data["message_label"]
        == MESSAGE_STATE_LABELS[MESSAGE_STATE_READY_FOR_COLLECTION]
    )
    assert "Outstanding Balance: ₹350.50" in data["message"]


def test_cancelled_order_400(client, staff):
    order = create_order(status=OrderStatus.CANCELLED)
    response = client.get(prepare_url(order.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST
    assert response.data["success"] is False
    assert response.data["error"]["code"] == "validation_error"


def test_missing_order_404(client, staff):
    response = client.get(prepare_url(999999), **_auth(staff))
    assert response.status_code == http_status.HTTP_404_NOT_FOUND
    assert response.data["success"] is False
    assert response.data["error"]["code"] == "not_found"


def test_endpoint_is_get_only(client, staff):
    order = create_order()
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)(prepare_url(order.id), **_auth(staff))
        assert response.status_code == http_status.HTTP_405_METHOD_NOT_ALLOWED


def test_prepare_never_mutates_business_records(client, staff):
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    counts = (
        Order.objects.count(),
        Invoice.objects.count(),
        CustomerPayment.objects.count(),
        Customer.objects.count(),
    )
    order_before = Order.objects.get(pk=order.pk)
    for status in (OrderStatus.NEW, OrderStatus.STITCHING, OrderStatus.READY):
        order.status = status
        order.save(update_fields=["status"])
        response = client.get(prepare_url(order.id), **_auth(staff))
        assert response.status_code == http_status.HTTP_200_OK
        assert Order.objects.get(pk=order.pk).status == status
    assert (
        Order.objects.count(),
        Invoice.objects.count(),
        CustomerPayment.objects.count(),
        Customer.objects.count(),
    ) == counts
    order_after = Order.objects.get(pk=order.pk)
    assert order_after.total_amount == order_before.total_amount
    assert order_after.status == OrderStatus.READY


# ---------------------------------------------------------------------------
# Privacy exclusions
# ---------------------------------------------------------------------------


def test_auto_privacy_exclusions():
    customer = create_customer(
        full_name="Ravi Kumar",
        notes="INTERNAL: prefers no home visits.",
    )
    order = create_order(
        customer=customer,
        notes="INTERNAL SECRET note must never appear.",
    )
    for status in (OrderStatus.NEW, OrderStatus.CUTTING, OrderStatus.READY):
        order.status = status
        order.save(update_fields=["status"])
        message = build_automatic_order_communication(order)["message"]
        assert "INTERNAL SECRET note must never appear." not in message
        assert "INTERNAL: prefers no home visits." not in message
        if order.customer.alternate_mobile_number:
            assert order.customer.alternate_mobile_number not in message


def test_no_undefined_or_null_placeholders():
    order = create_order(status=OrderStatus.READY)
    for status in (OrderStatus.NEW, OrderStatus.CUTTING, OrderStatus.READY):
        order.status = status
        order.save(update_fields=["status"])
        message = build_automatic_order_communication(order)["message"]
        assert "undefined" not in message.lower()
        assert "null" not in message.lower()
        assert "None" not in message
