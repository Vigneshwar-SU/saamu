"""Phase 19 operational-reminder preparation tests.

Covers both reminder types, eligible and ineligible states (including terminal
orders and invalid states), deterministic derived candidates, agreement with
the authoritative payment summary and with Phase 18 message preparation,
phone normalization / missing recipients, RBAC and HTTP contracts, idempotency
of repeated evaluation, no business-data mutation, and privacy exclusions.
"""

import pytest
from rest_framework import status as http_status

from apps.authentication.tests.helpers import auth_header
from apps.billing.communications import (
    MESSAGE_TYPE_PAYMENT_BALANCE,
    MESSAGE_TYPE_READY_FOR_COLLECTION,
    build_order_communication,
    format_inr,
)
from apps.billing.models import CustomerPayment, Invoice
from apps.billing.reminders import (
    REASON_NO_INVOICE,
    REASON_NO_OUTSTANDING_BALANCE,
    REASON_ORDER_NOT_READY,
    REASON_ORDER_TERMINAL,
    REMINDER_BALANCE_OUTSTANDING,
    REMINDER_READY_FOR_COLLECTION,
    REMINDER_TYPES,
    ReminderNotEligible,
    build_pending_reminders,
    build_reminder_candidate,
    evaluate_reminder_eligibility,
    parse_reminder_id,
    reminder_id,
)
from apps.billing.services import order_payment_summary
from apps.billing.tests.helpers import create_invoice, create_order, create_payment
from apps.customers.models import Customer
from apps.customers.tests.helpers import create_customer, make_owner, make_staff
from apps.orders.models import Order, OrderStatus

pytestmark = pytest.mark.django_db


def list_url():
    return "/api/v1/communications/reminders/"


def prepare_url(reminder):
    return f"/api/v1/communications/reminders/{reminder}/prepare/"


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


# ---------------------------------------------------------------------------
# Eligibility: ready for collection
# ---------------------------------------------------------------------------


def test_ready_for_collection_eligible_when_ready():
    order = create_order(status=OrderStatus.READY)
    eligible, code, _message = evaluate_reminder_eligibility(
        order, REMINDER_READY_FOR_COLLECTION
    )
    assert eligible is True
    assert code == REMINDER_READY_FOR_COLLECTION


def test_ready_for_collection_not_ready():
    order = create_order(status=OrderStatus.STITCHING)
    eligible, code, _message = evaluate_reminder_eligibility(
        order, REMINDER_READY_FOR_COLLECTION
    )
    assert eligible is False
    assert code == REASON_ORDER_NOT_READY


def test_ready_for_collection_terminal_orders_excluded():
    for status in (OrderStatus.COLLECTED, OrderStatus.CANCELLED):
        order = create_order(status=status)
        eligible, code, _message = evaluate_reminder_eligibility(
            order, REMINDER_READY_FOR_COLLECTION
        )
        assert eligible is False
        assert code == REASON_ORDER_TERMINAL


def test_ready_candidate_builds_phase_18_message():
    order = create_order(status=OrderStatus.READY)
    candidate = build_reminder_candidate(order, REMINDER_READY_FOR_COLLECTION)
    assert candidate["id"] == reminder_id(REMINDER_READY_FOR_COLLECTION, order.id)
    assert "Good news! Your order is ready for collection." in candidate["message"]


# ---------------------------------------------------------------------------
# Eligibility: balance outstanding
# ---------------------------------------------------------------------------


def test_balance_outstanding_eligible_when_invoiced_with_balance():
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    eligible, code, message = evaluate_reminder_eligibility(
        order, REMINDER_BALANCE_OUTSTANDING
    )
    assert eligible is True
    assert code == REMINDER_BALANCE_OUTSTANDING
    assert (
        f"{format_inr(order_payment_summary(order)['outstanding_balance'])}" in message
    )


def test_balance_outstanding_no_invoice_ineligible():
    order = create_order()
    eligible, code, _message = evaluate_reminder_eligibility(
        order, REMINDER_BALANCE_OUTSTANDING
    )
    assert eligible is False
    assert code == REASON_NO_INVOICE


def test_balance_outstanding_zero_balance_ineligible():
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(
        invoice, amount="450.50", payment_type=CustomerPayment.PaymentType.FINAL
    )
    eligible, code, _message = evaluate_reminder_eligibility(
        order, REMINDER_BALANCE_OUTSTANDING
    )
    assert eligible is False
    assert code == REASON_NO_OUTSTANDING_BALANCE


def test_balance_outstanding_terminal_orders_excluded():
    for status in (OrderStatus.COLLECTED, OrderStatus.CANCELLED):
        order = create_order(status=status)
        invoice = create_invoice(order=order)
        create_payment(invoice, amount="100.00")
        eligible, code, _message = evaluate_reminder_eligibility(
            order, REMINDER_BALANCE_OUTSTANDING
        )
        assert eligible is False
        assert code == REASON_ORDER_TERMINAL


def test_balance_candidate_builds_phase_18_message():
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    candidate = build_reminder_candidate(order, REMINDER_BALANCE_OUTSTANDING)
    assert candidate["id"] == reminder_id(REMINDER_BALANCE_OUTSTANDING, order.id)
    assert "Payment summary for your order." in candidate["message"]
    assert "Balance: ₹350.50" in candidate["message"]


# ---------------------------------------------------------------------------
# Unsupported types and id parsing
# ---------------------------------------------------------------------------


def test_unsupported_reminder_type_rejected():
    order = create_order()
    with pytest.raises(ValueError):
        evaluate_reminder_eligibility(order, "SEND_NOW")
    with pytest.raises(ValueError):
        build_reminder_candidate(order, "SEND_NOW")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (f"{REMINDER_READY_FOR_COLLECTION}_12", (REMINDER_READY_FOR_COLLECTION, 12)),
        (f"{REMINDER_BALANCE_OUTSTANDING}_7", (REMINDER_BALANCE_OUTSTANDING, 7)),
        ("SEND_NOW_12", None),
        (f"{REMINDER_READY_FOR_COLLECTION}_abc", None),
        ("12", None),
        ("READY_FOR_COLLECTION", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_reminder_id(value, expected):
    assert parse_reminder_id(value) == expected


def test_reminder_id_round_trip():
    assert parse_reminder_id(reminder_id(REMINDER_BALANCE_OUTSTANDING, 5)) == (
        REMINDER_BALANCE_OUTSTANDING,
        5,
    )


# ---------------------------------------------------------------------------
# Pending-reminders derivation
# ---------------------------------------------------------------------------


def test_pending_reminders_include_only_eligible():
    # READY, no invoice -> ready-for-collection only (balance requires an invoice).
    ready_unbilled = create_order(status=OrderStatus.READY)
    # STITCHING with invoice + balance -> balance only (not ready).
    stitching_billed = create_order(status=OrderStatus.STITCHING)
    create_payment(create_invoice(order=stitching_billed), amount="50.00")
    # READY with invoice + balance -> both.
    ready_billed = create_order(status=OrderStatus.READY)
    create_payment(create_invoice(order=ready_billed), amount="100.00")
    # COLLECTED with balance -> none (terminal).
    collected = create_order(status=OrderStatus.COLLECTED)
    create_payment(create_invoice(order=collected), amount="100.00")
    # CANCELLED with balance -> none (terminal).
    cancelled = create_order(status=OrderStatus.CANCELLED)
    create_payment(create_invoice(order=cancelled), amount="100.00")
    # NEW without invoice -> none (not ready, no invoice).
    create_order()
    # READY fully paid -> ready-for-collection only (balance settled).
    ready_paid = create_order(status=OrderStatus.READY)
    create_payment(
        create_invoice(order=ready_paid),
        amount="450.50",
        payment_type=CustomerPayment.PaymentType.FINAL,
    )

    reminders = build_pending_reminders()
    actual_ids = {reminder["id"] for reminder in reminders}
    expected_ids = {
        reminder_id(REMINDER_READY_FOR_COLLECTION, ready_unbilled.id),
        reminder_id(REMINDER_BALANCE_OUTSTANDING, stitching_billed.id),
        reminder_id(REMINDER_READY_FOR_COLLECTION, ready_billed.id),
        reminder_id(REMINDER_BALANCE_OUTSTANDING, ready_billed.id),
        reminder_id(REMINDER_READY_FOR_COLLECTION, ready_paid.id),
    }
    assert actual_ids == expected_ids
    assert collected.id not in {r["order"]["id"] for r in reminders}
    assert cancelled.id not in {r["order"]["id"] for r in reminders}


def test_pending_reminders_are_deterministic_and_ordered():
    first = create_order(status=OrderStatus.READY)
    second = create_order(status=OrderStatus.STITCHING)
    create_payment(create_invoice(order=second), amount="50.00")
    third = create_order(status=OrderStatus.READY)
    create_payment(create_invoice(order=third), amount="100.00")

    reminders = build_pending_reminders()
    assert reminders == build_pending_reminders()

    order_ids = [r["order"]["id"] for r in reminders]
    assert order_ids == sorted(order_ids)
    # Within the same order, types follow the fixed REMINDER_TYPES order.
    same_order = [r for r in reminders if r["order"]["id"] == third.id]
    assert [r["reminder_type"] for r in same_order] == list(REMINDER_TYPES)


def test_pending_reminders_message_agrees_with_phase_18():
    order = create_order(status=OrderStatus.READY)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    reminders = {
        r["reminder_type"]: r
        for r in build_pending_reminders()
        if r["order"]["id"] == order.id
    }

    ready_candidate = reminders[REMINDER_READY_FOR_COLLECTION]
    expected_ready = build_order_communication(order, MESSAGE_TYPE_READY_FOR_COLLECTION)
    assert ready_candidate["message"] == expected_ready["message"]
    assert ready_candidate["phone_number"] == expected_ready["phone_number"]
    assert ready_candidate["whatsapp_url"] == expected_ready["whatsapp_url"]

    balance_candidate = reminders[REMINDER_BALANCE_OUTSTANDING]
    expected_balance = build_order_communication(order, MESSAGE_TYPE_PAYMENT_BALANCE)
    assert balance_candidate["message"] == expected_balance["message"]
    assert balance_candidate["phone_number"] == expected_balance["phone_number"]
    assert balance_candidate["whatsapp_url"] == expected_balance["whatsapp_url"]


def test_balance_candidate_agrees_with_authoritative_summary():
    order = create_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="150.00")
    summary = order_payment_summary(order)
    candidate = build_reminder_candidate(order, REMINDER_BALANCE_OUTSTANDING)
    assert summary["has_invoice"] is True
    assert (
        summary["outstanding_balance"] == summary["order_total"] - summary["total_paid"]
    )
    assert f"Total: {format_inr(summary['order_total'])}" in candidate["message"]
    assert f"Amount Paid: {format_inr(summary['total_paid'])}" in candidate["message"]
    assert (
        f"Balance: {format_inr(summary['outstanding_balance'])}" in candidate["message"]
    )


# ---------------------------------------------------------------------------
# Phone normalization and missing recipients
# ---------------------------------------------------------------------------


def test_candidate_normalizes_phone():
    order = create_order(status=OrderStatus.READY)
    candidate = build_reminder_candidate(order, REMINDER_READY_FOR_COLLECTION)
    assert candidate["phone_number"] == "919876543210"
    assert candidate["whatsapp_url"].startswith("https://wa.me/919876543210?text=")


@pytest.mark.parametrize("mobile", ["not-a-number", "", "123"])
def test_candidate_missing_or_invalid_phone(mobile):
    customer = create_customer(mobile_number=mobile)
    order = create_order(customer=customer, status=OrderStatus.READY)
    candidate = build_reminder_candidate(order, REMINDER_READY_FOR_COLLECTION)
    assert candidate["phone_number"] is None
    assert candidate["whatsapp_url"] is None


# ---------------------------------------------------------------------------
# API: list
# ---------------------------------------------------------------------------


def test_list_response_shape(client, staff):
    order = create_order(status=OrderStatus.READY)
    response = client.get(list_url(), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    body = response.data
    assert set(body) == {"success", "data"}
    assert body["success"] is True
    assert set(body["data"]) == {"count", "next", "previous", "results"}
    assert body["data"]["count"] == 1
    results = body["data"]["results"]
    assert len(results) == 1
    result = results[0]
    assert result["id"] == reminder_id(REMINDER_READY_FOR_COLLECTION, order.id)
    assert set(result) == {
        "id",
        "reminder_type",
        "reminder_type_label",
        "order",
        "customer",
        "eligibility",
        "message",
        "phone_number",
        "whatsapp_url",
    }
    assert result["eligibility"]["eligible"] is True
    assert result["message"]


def test_list_anonymous_gets_401(client):
    create_order(status=OrderStatus.READY)
    response = client.get(list_url())
    assert response.status_code == http_status.HTTP_401_UNAUTHORIZED


def test_list_owner_and_staff_can_read(client, owner, staff):
    create_order(status=OrderStatus.READY)
    for user in (owner, staff):
        response = client.get(list_url(), **_auth(user))
        assert response.status_code == http_status.HTTP_200_OK
        assert response.data["success"] is True


def test_list_is_get_only(client, staff):
    create_order(status=OrderStatus.READY)
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)(list_url(), **_auth(staff))
        assert response.status_code == http_status.HTTP_405_METHOD_NOT_ALLOWED


def test_list_is_paginated(client, staff):
    for _ in range(22):
        create_order(status=OrderStatus.READY)
    first = client.get(list_url(), **_auth(staff))
    assert first.status_code == http_status.HTTP_200_OK
    assert first.data["data"]["count"] == 22
    assert len(first.data["data"]["results"]) == 6
    assert first.data["data"]["next"] is not None
    assert first.data["data"]["previous"] is None

    second = client.get(list_url(), {"page": 2}, **_auth(staff))
    assert second.status_code == http_status.HTTP_200_OK
    assert len(second.data["data"]["results"]) == 6
    assert second.data["data"]["next"] is not None
    assert second.data["data"]["previous"] is not None

    third = client.get(list_url(), {"page": 4}, **_auth(staff))
    assert third.status_code == http_status.HTTP_200_OK
    assert len(third.data["data"]["results"]) == 4
    assert third.data["data"]["next"] is None
    assert third.data["data"]["previous"] is not None


def test_list_is_deterministic(client, staff):
    create_order(status=OrderStatus.READY)
    order = create_order(status=OrderStatus.STITCHING)
    create_payment(create_invoice(order=order), amount="50.00")
    first = client.get(list_url(), **_auth(staff)).data
    second = client.get(list_url(), **_auth(staff)).data
    assert first == second


# ---------------------------------------------------------------------------
# API: prepare
# ---------------------------------------------------------------------------


def test_prepare_returns_candidate(client, staff):
    order = create_order(status=OrderStatus.READY)
    reminder = reminder_id(REMINDER_READY_FOR_COLLECTION, order.id)
    response = client.get(prepare_url(reminder), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    assert response.data["success"] is True
    assert response.data["data"]["id"] == reminder
    assert "Good news!" in response.data["data"]["message"]


def test_prepare_anonymous_gets_401(client):
    order = create_order(status=OrderStatus.READY)
    response = client.get(
        prepare_url(reminder_id(REMINDER_READY_FOR_COLLECTION, order.id))
    )
    assert response.status_code == http_status.HTTP_401_UNAUTHORIZED


def test_prepare_owner_and_staff_can_read(client, owner, staff):
    order = create_order(status=OrderStatus.READY)
    reminder = reminder_id(REMINDER_READY_FOR_COLLECTION, order.id)
    for user in (owner, staff):
        response = client.get(prepare_url(reminder), **_auth(user))
        assert response.status_code == http_status.HTTP_200_OK


@pytest.mark.parametrize(
    "reminder",
    [
        "BOGUS_12",
        "NOT_A_TYPE_12",
        "READY_FOR_COLLECTION_abc",
        "12",
        "READY_FOR_COLLECTION",
    ],
)
def test_prepare_invalid_id_400(client, staff, reminder):
    response = client.get(prepare_url(reminder), **_auth(staff))
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST
    assert response.data["success"] is False
    assert response.data["error"]["code"] == "validation_error"


def test_prepare_missing_order_404(client, staff):
    response = client.get(
        prepare_url(reminder_id(REMINDER_READY_FOR_COLLECTION, 999999)),
        **_auth(staff),
    )
    assert response.status_code == http_status.HTTP_404_NOT_FOUND
    assert response.data["error"]["code"] == "not_found"


def test_prepare_stale_ready_reminder_400(client, staff):
    order = create_order(status=OrderStatus.READY)
    reminder = reminder_id(REMINDER_READY_FOR_COLLECTION, order.id)
    assert client.get(prepare_url(reminder), **_auth(staff)).status_code == (
        http_status.HTTP_200_OK
    )
    order.status = OrderStatus.STITCHING
    order.save(update_fields=["status"])
    response = client.get(prepare_url(reminder), **_auth(staff))
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST
    assert response.data["error"]["code"] == "validation_error"
    assert REASON_ORDER_NOT_READY in str(
        response.data["error"]["details"]["reminder_id"]
    )


def test_prepare_stale_balance_reminder_400(client, staff):
    order = create_order(status=OrderStatus.STITCHING)
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    reminder = reminder_id(REMINDER_BALANCE_OUTSTANDING, order.id)
    assert client.get(prepare_url(reminder), **_auth(staff)).status_code == (
        http_status.HTTP_200_OK
    )
    create_payment(
        invoice, amount="350.50", payment_type=CustomerPayment.PaymentType.FINAL
    )
    response = client.get(prepare_url(reminder), **_auth(staff))
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST
    assert REASON_NO_OUTSTANDING_BALANCE in str(
        response.data["error"]["details"]["reminder_id"]
    )


def test_prepare_is_get_only(client, staff):
    order = create_order(status=OrderStatus.READY)
    reminder = prepare_url(reminder_id(REMINDER_READY_FOR_COLLECTION, order.id))
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)(reminder, **_auth(staff))
        assert response.status_code == http_status.HTTP_405_METHOD_NOT_ALLOWED


def test_prepare_is_deterministic(client, staff):
    order = create_order(status=OrderStatus.READY)
    reminder = prepare_url(reminder_id(REMINDER_READY_FOR_COLLECTION, order.id))
    first = client.get(reminder, **_auth(staff)).data
    second = client.get(reminder, **_auth(staff)).data
    assert first == second


# ---------------------------------------------------------------------------
# No mutation and privacy
# ---------------------------------------------------------------------------


def test_reminders_never_mutate_business_records(client, staff):
    ready = create_order(status=OrderStatus.READY)
    billed = create_order(status=OrderStatus.STITCHING)
    invoice = create_invoice(order=billed)
    create_payment(invoice, amount="100.00")

    counts = (
        Order.objects.count(),
        Invoice.objects.count(),
        CustomerPayment.objects.count(),
        Customer.objects.count(),
    )
    ready_before = Order.objects.get(pk=ready.pk)
    billed_before = Order.objects.get(pk=billed.pk)

    list_response = client.get(list_url(), **_auth(staff))
    assert list_response.status_code == http_status.HTTP_200_OK
    for candidate in list_response.data["data"]["results"]:
        prepare_response = client.get(prepare_url(candidate["id"]), **_auth(staff))
        assert prepare_response.status_code == http_status.HTTP_200_OK

    assert (
        Order.objects.count(),
        Invoice.objects.count(),
        CustomerPayment.objects.count(),
        Customer.objects.count(),
    ) == counts
    assert Order.objects.get(pk=ready.pk).status == ready_before.status
    assert Order.objects.get(pk=billed.pk).total_amount == billed_before.total_amount
    assert Order.objects.get(pk=billed.pk).status == billed_before.status


def test_messages_exclude_internal_notes():
    customer = create_customer(
        full_name="Ravi Kumar",
        notes="INTERNAL: prefers no home visits.",
    )
    order = create_order(
        customer=customer,
        status=OrderStatus.READY,
        notes="INTERNAL SECRET note must never appear.",
    )
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    for reminder in build_pending_reminders():
        assert "INTERNAL SECRET note must never appear." not in reminder["message"]
        assert "INTERNAL: prefers no home visits." not in reminder["message"]


def test_phone_number_only_in_dedicated_field():
    customer = create_customer(mobile_number="9876543210")
    order = create_order(customer=customer, status=OrderStatus.READY)
    candidate = build_reminder_candidate(order, REMINDER_READY_FOR_COLLECTION)
    assert candidate["phone_number"] == "919876543210"
    assert "9876543210" not in candidate["message"]
    assert "919876543210" not in candidate["message"]
    assert candidate["customer"]["full_name"] != "919876543210"


def test_reminder_not_eligible_carries_stable_code():
    order = create_order(status=OrderStatus.NEW)
    with pytest.raises(ReminderNotEligible) as excinfo:
        build_reminder_candidate(order, REMINDER_READY_FOR_COLLECTION)
    assert excinfo.value.code == REASON_ORDER_NOT_READY
