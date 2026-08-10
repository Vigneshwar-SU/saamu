"""Reminders V1 derivation and API tests.

Covers all automatic reminder categories (overdue, due today/tomorrow, ready
for pickup, payment outstanding, tailor workload, measurement missing,
customer follow-up), manual reminders, deterministic merged candidates,
summary counts, filtering, pagination, RBAC, and the manual reminder CRUD /
complete / cancel flow.
"""

from datetime import date, timedelta

import pytest
from rest_framework import status as http_status

from apps.authentication.tests.helpers import auth_header
from apps.billing.models import ManualReminder, ShopDetails
from apps.billing.reminder_service import (
    REMINDER_CUSTOMER_FOLLOW_UP,
    REMINDER_MANUAL,
    REMINDER_MEASUREMENT_MISSING,
    REMINDER_ORDER_DUE_TODAY,
    REMINDER_ORDER_DUE_TOMORROW,
    REMINDER_OVERDUE_ORDER,
    REMINDER_PAYMENT_OUTSTANDING,
    REMINDER_READY_FOR_PICKUP,
    REMINDER_TAILOR_WORKLOAD,
    REMINDER_TYPE_LABELS,
    REMINDER_TYPES,
    build_pending_reminder_candidates,
    reminder_summary,
)
from apps.billing.tests.helpers import create_invoice, create_order, create_payment
from apps.customers.models import Customer
from apps.customers.tests.helpers import create_customer, make_owner, make_staff
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.tailors.models import Tailor, WorkAssignment
from apps.tailors.tests.helpers import create_assignment, create_tailor

pytestmark = pytest.mark.django_db


def list_url():
    return "/api/v1/reminders/"


def summary_url():
    return "/api/v1/reminders/summary/"


def manual_list_url():
    return "/api/v1/reminders/manual/"


def manual_detail_url(reminder_id):
    return f"/api/v1/reminders/manual/{reminder_id}/"


def manual_complete_url(reminder_id):
    return f"/api/v1/reminders/manual/{reminder_id}/complete/"


def manual_cancel_url(reminder_id):
    return f"/api/v1/reminders/manual/{reminder_id}/cancel/"


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _complete_snapshot(garment_type):
    if garment_type == "SHIRT":
        return {
            "neck_circumference": 15.5,
            "chest_circumference": 40.0,
            "waist_circumference": 34.0,
            "shoulder_width": 18.5,
            "sleeve_length": 25.0,
            "shirt_length": 30.0,
        }
    return {
        "waist_circumference": 34.0,
        "hip_circumference": 40.0,
        "length": 41.0,
    }


def create_clean_order(customer=None, **extra):
    """Create an order whose items carry complete measurement snapshots.

    The shared billing helper intentionally leaves ``measurement_snapshot``
    empty; a complete snapshot avoids spurious MEASUREMENT_MISSING reminders.
    """
    order = create_order(customer=customer, **extra)
    for item in order.items.all():
        item.measurement_snapshot = _complete_snapshot(item.garment_type)
        item.save(update_fields=["measurement_snapshot"])
    return order


def create_manual_reminder(
    title="Call Ravi",
    reminder_date=None,
    priority=ManualReminder.Priority.MEDIUM,
    status=ManualReminder.Status.PENDING,
    customer=None,
    order=None,
    **extra,
):
    return ManualReminder.objects.create(
        title=title,
        description=extra.pop("description", ""),
        reminder_date=reminder_date or date.today(),
        priority=priority,
        status=status,
        customer=customer,
        order=order,
        **extra,
    )


def _ids(candidates):
    return {c["id"] for c in candidates}


def _types(candidates):
    return {c["reminder_type"] for c in candidates}


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


# ---------------------------------------------------------------------------
# Overdue / due date reminders
# ---------------------------------------------------------------------------


def test_overdue_order_candidate():
    past = date.today() - timedelta(days=5)
    order = create_clean_order(expected_delivery_date=past)
    candidates = build_pending_reminder_candidates()
    by_type = {
        c["reminder_type"]: c for c in candidates if c["order"]["id"] == order.id
    }
    assert (
        by_type[REMINDER_OVERDUE_ORDER]["id"] == f"{REMINDER_OVERDUE_ORDER}_{order.id}"
    )
    assert by_type[REMINDER_OVERDUE_ORDER]["date"] == past


def test_overdue_requires_due_date():
    order = create_clean_order()  # no expected delivery date
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_OVERDUE_ORDER}_{order.id}" not in _ids(candidates)


def test_overdue_future_date_not_overdue():
    future = date.today() + timedelta(days=10)
    order = create_clean_order(expected_delivery_date=future)
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_OVERDUE_ORDER}_{order.id}" not in _ids(candidates)


def test_terminal_orders_excluded():
    past = date.today() - timedelta(days=3)
    for status in (OrderStatus.COLLECTED, OrderStatus.CANCELLED):
        order = create_clean_order(status=status, expected_delivery_date=past)
        candidates = build_pending_reminder_candidates()
        assert f"{REMINDER_OVERDUE_ORDER}_{order.id}" not in _ids(candidates)
        assert f"{REMINDER_ORDER_DUE_TODAY}_{order.id}" not in _ids(candidates)
        assert f"{REMINDER_ORDER_DUE_TOMORROW}_{order.id}" not in _ids(candidates)


def test_due_today_candidate():
    today = date.today()
    order = create_clean_order(expected_delivery_date=today)
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_ORDER_DUE_TODAY}_{order.id}" in _ids(candidates)


def test_due_tomorrow_candidate():
    tomorrow = date.today() + timedelta(days=1)
    order = create_clean_order(expected_delivery_date=tomorrow)
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_ORDER_DUE_TOMORROW}_{order.id}" in _ids(candidates)


def test_due_date_reminders_are_mutually_exclusive():
    today = date.today()
    order = create_clean_order(expected_delivery_date=today)
    reminders = [
        c for c in build_pending_reminder_candidates() if c["order"]["id"] == order.id
    ]
    assert (
        len([c for c in reminders if c["reminder_type"].startswith("ORDER_DUE")]) == 1
    )


# ---------------------------------------------------------------------------
# Ready for pickup
# ---------------------------------------------------------------------------


def test_ready_for_pickup_candidate_with_whatsapp():
    order = create_clean_order(status=OrderStatus.READY)
    candidates = build_pending_reminder_candidates()
    reminder = next(
        c for c in candidates if c["id"] == f"{REMINDER_READY_FOR_PICKUP}_{order.id}"
    )
    assert reminder["message"]
    assert "ready for collection" in reminder["message"].lower()
    assert reminder["phone_number"] == "919876543210"
    assert reminder["whatsapp_url"].startswith("https://wa.me/919876543210?text=")
    assert reminder["action"] == {
        "kind": "order",
        "target_id": order.id,
        "label": "View Order",
    }


def test_ready_for_pickup_only_when_ready():
    order = create_clean_order(status=OrderStatus.STITCHING)
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_READY_FOR_PICKUP}_{order.id}" not in _ids(candidates)


# ---------------------------------------------------------------------------
# Payment outstanding
# ---------------------------------------------------------------------------


def test_payment_outstanding_candidate_with_whatsapp():
    order = create_clean_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="100.00")
    candidates = build_pending_reminder_candidates()
    reminder = next(
        c for c in candidates if c["id"] == f"{REMINDER_PAYMENT_OUTSTANDING}_{order.id}"
    )
    assert "Balance: ₹350.50" in reminder["message"]
    assert reminder["whatsapp_url"].startswith("https://wa.me/919876543210?text=")


def test_payment_outstanding_no_invoice_excluded():
    order = create_clean_order()
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_PAYMENT_OUTSTANDING}_{order.id}" not in _ids(candidates)


def test_payment_outstanding_settled_excluded():
    order = create_clean_order()
    invoice = create_invoice(order=order)
    create_payment(invoice, amount="450.50")
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_PAYMENT_OUTSTANDING}_{order.id}" not in _ids(candidates)


# ---------------------------------------------------------------------------
# Tailor workload
# ---------------------------------------------------------------------------


def test_tailor_workload_candidate():
    order = create_clean_order()
    item = order.items.first()
    tailor = create_tailor()
    create_assignment(tailor, item, assigned_quantity=2, completed_quantity=1)
    candidates = build_pending_reminder_candidates()
    reminder = next(
        c for c in candidates if c["id"] == f"{REMINDER_TAILOR_WORKLOAD}_{tailor.id}"
    )
    assert reminder["tailor"]["id"] == tailor.id
    assert reminder["tailor"]["outstanding_quantity"] == 1
    assert reminder["action"] == {
        "kind": "tailor",
        "target_id": tailor.id,
        "label": "View Tailor",
    }


def test_tailor_workload_skips_completed_work():
    order = create_clean_order()
    item = order.items.first()
    tailor = create_tailor()
    create_assignment(
        tailor,
        item,
        assigned_quantity=2,
        completed_quantity=2,
        status=WorkAssignment.Status.COMPLETED,
    )
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_TAILOR_WORKLOAD}_{tailor.id}" not in _ids(candidates)


def test_tailor_workload_skips_inactive_tailors():
    order = create_clean_order()
    item = order.items.first()
    tailor = create_tailor(is_active=False)
    create_assignment(tailor, item, assigned_quantity=2)
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_TAILOR_WORKLOAD}_{tailor.id}" not in _ids(candidates)


# ---------------------------------------------------------------------------
# Measurement missing
# ---------------------------------------------------------------------------


def test_measurement_missing_when_reference_missing():
    order = create_clean_order()
    item = order.items.first()
    item.measurement = None
    item.save(update_fields=["measurement"])
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_MEASUREMENT_MISSING}_{item.id}" in _ids(candidates)


def test_measurement_missing_when_snapshot_incomplete():
    order = create_clean_order()
    item = order.items.first()
    item.measurement_snapshot = {"neck_circumference": 15.5}
    item.save(update_fields=["measurement_snapshot"])
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_MEASUREMENT_MISSING}_{item.id}" in _ids(candidates)


def test_measurement_complete_no_reminder():
    order = create_clean_order()
    item = order.items.first()
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_MEASUREMENT_MISSING}_{item.id}" not in _ids(candidates)


def test_measurement_missing_skips_terminal_orders():
    order = create_clean_order(status=OrderStatus.CANCELLED)
    item = order.items.first()
    item.measurement = None
    item.save(update_fields=["measurement"])
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_MEASUREMENT_MISSING}_{item.id}" not in _ids(candidates)


# ---------------------------------------------------------------------------
# Customer follow-up
# ---------------------------------------------------------------------------


def test_customer_follow_up_candidate():
    customer = create_customer()
    old_date = date.today() - timedelta(days=300)
    create_clean_order(customer=customer, order_date=old_date)
    candidates = build_pending_reminder_candidates()
    reminder = next(
        c
        for c in candidates
        if c["id"] == f"{REMINDER_CUSTOMER_FOLLOW_UP}_{customer.id}"
    )
    assert reminder["date"] == old_date
    assert reminder["action"] == {
        "kind": "customer",
        "target_id": customer.id,
        "label": "View Customer",
    }
    assert "300 day(s) ago" in reminder["description"]


def test_customer_follow_up_skips_recent_orders():
    customer = create_customer()
    create_clean_order(customer=customer, order_date=date.today() - timedelta(days=10))
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_CUSTOMER_FOLLOW_UP}_{customer.id}" not in _ids(candidates)


def test_customer_follow_up_skips_archived_customers():
    customer = create_customer(is_active=False)
    create_clean_order(customer=customer, order_date=date.today() - timedelta(days=300))
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_CUSTOMER_FOLLOW_UP}_{customer.id}" not in _ids(candidates)


def test_customer_follow_up_skips_never_ordered():
    customer = create_customer()
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_CUSTOMER_FOLLOW_UP}_{customer.id}" not in _ids(candidates)


def test_customer_follow_up_uses_configured_threshold():
    details = ShopDetails.shop_details()
    details.customer_follow_up_months = 12
    details.save(update_fields=["customer_follow_up_months"])
    customer = create_customer()
    old_date = date.today() - timedelta(days=200)
    create_clean_order(customer=customer, order_date=old_date)
    candidates = build_pending_reminder_candidates()
    assert f"{REMINDER_CUSTOMER_FOLLOW_UP}_{customer.id}" not in _ids(candidates)
    assert "12 month(s)" not in "".join(
        c["description"]
        for c in candidates
        if c["id"].startswith(REMINDER_CUSTOMER_FOLLOW_UP)
    )


# ---------------------------------------------------------------------------
# Manual reminders
# ---------------------------------------------------------------------------


def test_manual_reminder_candidate_merged():
    create_manual_reminder(title="Follow up on fabric", reminder_date=date.today())
    candidates = build_pending_reminder_candidates()
    manual = [c for c in candidates if c["is_manual"]]
    assert len(manual) == 1
    assert manual[0]["reminder_type"] == REMINDER_MANUAL
    assert manual[0]["priority"] == ManualReminder.Priority.MEDIUM
    assert manual[0]["date"] == date.today()


def test_manual_reminder_only_pending_included():
    create_manual_reminder(title="Active")
    create_manual_reminder(title="Done", status=ManualReminder.Status.COMPLETED)
    create_manual_reminder(title="Gone", status=ManualReminder.Status.CANCELLED)
    candidates = build_pending_reminder_candidates()
    titles = [c["title"] for c in candidates if c["is_manual"]]
    assert titles == ["Active"]


# ---------------------------------------------------------------------------
# Determinism, ordering, summary
# ---------------------------------------------------------------------------


def test_candidates_are_deterministic():
    create_clean_order(status=OrderStatus.READY)
    create_manual_reminder()
    assert build_pending_reminder_candidates() == build_pending_reminder_candidates()


def test_candidates_ordered_by_date_then_id():
    older = date.today() - timedelta(days=30)
    order = create_clean_order(expected_delivery_date=older)
    reminder_ids = [
        c["id"] for c in build_pending_reminder_candidates() if c["date"] is not None
    ]
    assert reminder_ids == sorted(reminder_ids, key=lambda r: r)


def test_summary_counts():
    create_clean_order(expected_delivery_date=date.today() - timedelta(days=2))
    create_clean_order(status=OrderStatus.READY)
    customer = create_customer()
    create_clean_order(customer=customer, order_date=date.today() - timedelta(days=300))
    create_manual_reminder()
    summary = reminder_summary()
    assert summary["total"] == 4
    assert summary["by_type"][REMINDER_OVERDUE_ORDER] == 1
    assert summary["by_type"][REMINDER_READY_FOR_PICKUP] == 1
    assert summary["by_type"][REMINDER_CUSTOMER_FOLLOW_UP] == 1
    assert summary["by_type"][REMINDER_MANUAL] == 1
    assert summary["by_category"]["orders"] == 2
    assert summary["by_category"]["customers"] == 1
    assert summary["by_category"]["manual"] == 1
    for reminder_type in REMINDER_TYPES:
        assert summary["by_type"][reminder_type] >= 0
        assert summary["by_type"][reminder_type] == int(
            summary["by_type"][reminder_type]
        )


# ---------------------------------------------------------------------------
# API: list
# ---------------------------------------------------------------------------


def test_list_response_shape(client, staff):
    order = create_clean_order(status=OrderStatus.READY)
    response = client.get(list_url(), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    body = response.data
    assert body["success"] is True
    assert set(body["data"]) == {"count", "next", "previous", "results"}
    result = next(
        r
        for r in body["data"]["results"]
        if r["id"] == f"{REMINDER_READY_FOR_PICKUP}_{order.id}"
    )
    assert set(result) >= {
        "id",
        "reminder_type",
        "reminder_type_label",
        "category",
        "date",
        "priority",
        "title",
        "description",
        "order",
        "customer",
        "tailor",
        "action",
        "message",
        "phone_number",
        "whatsapp_url",
        "is_manual",
    }


def test_list_anonymous_gets_401(client):
    response = client.get(list_url())
    assert response.status_code == http_status.HTTP_401_UNAUTHORIZED


def test_list_owner_and_staff_can_read(client, owner, staff):
    create_clean_order(status=OrderStatus.READY)
    for user in (owner, staff):
        response = client.get(list_url(), **_auth(user))
        assert response.status_code == http_status.HTTP_200_OK
        assert response.data["success"] is True


def test_list_is_get_only(client, staff):
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)(list_url(), **_auth(staff))
        assert response.status_code == http_status.HTTP_405_METHOD_NOT_ALLOWED


def test_list_filter_by_type(client, staff):
    create_clean_order(expected_delivery_date=date.today() - timedelta(days=2))
    create_clean_order(status=OrderStatus.READY)
    response = client.get(list_url(), {"type": REMINDER_OVERDUE_ORDER}, **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    results = response.data["data"]["results"]
    assert results
    assert all(r["reminder_type"] == REMINDER_OVERDUE_ORDER for r in results)


def test_list_filter_invalid_type_400(client, staff):
    response = client.get(list_url(), {"type": "NOT_A_TYPE"}, **_auth(staff))
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST
    assert response.data["error"]["code"] == "validation_error"


def test_list_filter_by_category(client, staff):
    create_clean_order(status=OrderStatus.READY)
    create_manual_reminder()
    response = client.get(list_url(), {"category": "manual"}, **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    results = response.data["data"]["results"]
    assert results
    assert all(r["category"] == "manual" for r in results)


def test_list_filter_invalid_category_400(client, staff):
    response = client.get(list_url(), {"category": "bogus"}, **_auth(staff))
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST


def test_list_filter_by_priority_manual_only(client, staff):
    create_manual_reminder(priority=ManualReminder.Priority.HIGH)
    create_manual_reminder(priority=ManualReminder.Priority.LOW)
    response = client.get(
        list_url(), {"priority": ManualReminder.Priority.HIGH}, **_auth(staff)
    )
    assert response.status_code == http_status.HTTP_200_OK
    results = response.data["data"]["results"]
    assert results
    assert all(r["priority"] == ManualReminder.Priority.HIGH for r in results)


def test_list_filter_invalid_priority_400(client, staff):
    response = client.get(list_url(), {"priority": "WHATEVER"}, **_auth(staff))
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST


def test_list_filter_by_date(client, staff):
    due = date.today()
    order = create_clean_order(expected_delivery_date=due)
    create_clean_order(expected_delivery_date=date.today() + timedelta(days=5))
    response = client.get(list_url(), {"date": due.isoformat()}, **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    results = response.data["data"]["results"]
    assert results
    assert all(r["date"] == due for r in results)
    assert f"{REMINDER_ORDER_DUE_TODAY}_{order.id}" in _ids(results)


def test_list_filter_invalid_date_400(client, staff):
    response = client.get(list_url(), {"date": "not-a-date"}, **_auth(staff))
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST


def test_list_search_matches_order_number_and_customer(client, staff):
    customer = create_customer(full_name="Zorawar Singh")
    order = create_clean_order(customer=customer, status=OrderStatus.READY)
    response = client.get(list_url(), {"search": "Zorawar"}, **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    results = response.data["data"]["results"]
    assert f"{REMINDER_READY_FOR_PICKUP}_{order.id}" in _ids(results)

    response = client.get(list_url(), {"search": order.order_number}, **_auth(staff))
    assert f"{REMINDER_READY_FOR_PICKUP}_{order.id}" in _ids(
        response.data["data"]["results"]
    )


def test_list_search_returns_nothing_when_no_match(client, staff):
    create_clean_order(status=OrderStatus.READY)
    response = client.get(list_url(), {"search": "zzz-no-match"}, **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    assert response.data["data"]["results"] == []


def test_list_is_paginated(client, staff):
    for _ in range(22):
        create_clean_order(status=OrderStatus.READY)
    first = client.get(list_url(), **_auth(staff))
    assert first.data["data"]["count"] == 22
    assert len(first.data["data"]["results"]) == 6
    assert first.data["data"]["next"] is not None

    second = client.get(list_url(), {"page": 2}, **_auth(staff))
    assert len(second.data["data"]["results"]) == 6
    assert second.data["data"]["next"] is not None

    third = client.get(list_url(), {"page": 4}, **_auth(staff))
    assert len(third.data["data"]["results"]) == 4
    assert third.data["data"]["next"] is None


# ---------------------------------------------------------------------------
# API: summary
# ---------------------------------------------------------------------------


def test_summary_response(client, staff):
    create_clean_order(expected_delivery_date=date.today() - timedelta(days=2))
    response = client.get(summary_url(), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    body = response.data
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {"total", "by_type", "by_category"}
    assert data["by_type"][REMINDER_OVERDUE_ORDER] == 1
    assert data["total"] >= 1


def test_summary_anonymous_gets_401(client):
    response = client.get(summary_url())
    assert response.status_code == http_status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# API: manual reminder CRUD
# ---------------------------------------------------------------------------


def test_manual_create_staff_only(client, staff, owner):
    payload = {
        "title": "Call Ravi about cloth",
        "description": "Confirm the fabric choice.",
        "reminder_date": "2026-08-20",
        "priority": "HIGH",
    }
    staff_response = client.post(manual_list_url(), payload, **_auth(staff))
    assert staff_response.status_code == http_status.HTTP_201_CREATED
    body = staff_response.data
    assert body["title"] == payload["title"]
    assert body["priority"] == "HIGH"
    assert body["status"] == "PENDING"
    assert body["created_by_name"] == staff.username

    owner_response = client.post(
        manual_list_url(), payload, content_type="application/json", **_auth(owner)
    )
    assert owner_response.status_code == http_status.HTTP_403_FORBIDDEN


def test_manual_create_anonymous_gets_401(client):
    payload = {"title": "Reminder", "reminder_date": "2026-08-20"}
    response = client.post(manual_list_url(), payload)
    assert response.status_code == http_status.HTTP_401_UNAUTHORIZED


def test_manual_create_validation(client, staff):
    response = client.post(
        manual_list_url(), {"reminder_date": "2026-08-20"}, **_auth(staff)
    )
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST
    assert "title" in response.data["error"]["details"]


def test_manual_create_links_order_and_customer(client, staff):
    customer = create_customer()
    order = create_clean_order(customer=customer)
    response = client.post(
        manual_list_url(),
        {
            "title": "Order follow-up",
            "reminder_date": "2026-08-20",
            "customer": customer.id,
            "order": order.id,
        },
        **_auth(staff),
    )
    assert response.status_code == http_status.HTTP_201_CREATED
    body = response.data
    assert body["customer"]["id"] == customer.id
    assert body["order"]["id"] == order.id


def test_manual_create_order_infers_customer(client, staff):
    customer = create_customer()
    order = create_clean_order(customer=customer)
    response = client.post(
        manual_list_url(),
        {"title": "Order follow-up", "reminder_date": "2026-08-20", "order": order.id},
        **_auth(staff),
    )
    assert response.status_code == http_status.HTTP_201_CREATED
    assert response.data["customer"]["id"] == customer.id


def test_manual_create_rejects_mismatched_order_customer(client, staff):
    other = create_customer(full_name="Other Customer")
    order = create_clean_order(customer=other)
    response = client.post(
        manual_list_url(),
        {
            "title": "Bad link",
            "reminder_date": "2026-08-20",
            "customer": create_customer(full_name="Someone Else").id,
            "order": order.id,
        },
        **_auth(staff),
    )
    assert response.status_code == http_status.HTTP_400_BAD_REQUEST


def test_manual_list_and_detail(client, owner, staff):
    reminder = create_manual_reminder()
    for user in (owner, staff):
        response = client.get(manual_list_url(), **_auth(user))
        assert response.status_code == http_status.HTTP_200_OK
        assert response.data["count"] == 1

        detail = client.get(manual_detail_url(reminder.id), **_auth(user))
        assert detail.status_code == http_status.HTTP_200_OK
        assert detail.data["title"] == reminder.title


def test_manual_list_filters_status(client, staff):
    create_manual_reminder(title="Pending one")
    create_manual_reminder(
        title="Completed one", status=ManualReminder.Status.COMPLETED
    )
    pending = client.get(
        manual_list_url(), {"status": ManualReminder.Status.PENDING}, **_auth(staff)
    )
    assert pending.data["count"] == 1
    assert pending.data["results"][0]["title"] == "Pending one"

    completed = client.get(
        manual_list_url(), {"status": ManualReminder.Status.COMPLETED}, **_auth(staff)
    )
    assert completed.data["count"] == 1
    assert completed.data["results"][0]["title"] == "Completed one"


def test_manual_complete_flow(client, staff):
    reminder = create_manual_reminder()
    response = client.post(manual_complete_url(reminder.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    body = response.data
    assert body["success"] is True
    assert body["reminder"]["status"] == "COMPLETED"
    assert body["reminder"]["completed_by_name"] == staff.username
    reminder.refresh_from_db()
    assert reminder.status == ManualReminder.Status.COMPLETED
    assert reminder.completed_at is not None

    again = client.post(manual_complete_url(reminder.id), **_auth(staff))
    assert again.status_code == http_status.HTTP_400_BAD_REQUEST


def test_manual_cancel_flow(client, staff):
    reminder = create_manual_reminder()
    response = client.post(manual_cancel_url(reminder.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_200_OK
    assert response.data["reminder"]["status"] == "CANCELLED"
    reminder.refresh_from_db()
    assert reminder.status == ManualReminder.Status.CANCELLED

    again = client.post(manual_cancel_url(reminder.id), **_auth(staff))
    assert again.status_code == http_status.HTTP_400_BAD_REQUEST


def test_manual_complete_cancel_staff_only(client, owner):
    reminder = create_manual_reminder()
    response = client.post(manual_complete_url(reminder.id), **_auth(owner))
    assert response.status_code == http_status.HTTP_403_FORBIDDEN
    response = client.post(manual_cancel_url(reminder.id), **_auth(owner))
    assert response.status_code == http_status.HTTP_403_FORBIDDEN


def test_manual_completed_reminder_leaves_pending_list(client, staff):
    reminder = create_manual_reminder()
    client.post(manual_complete_url(reminder.id), **_auth(staff))
    response = client.get(list_url(), **_auth(staff))
    assert all(not r["is_manual"] for r in response.data["data"]["results"])


def test_manual_has_no_delete_route(client, staff):
    reminder = create_manual_reminder()
    response = client.delete(manual_detail_url(reminder.id), **_auth(staff))
    assert response.status_code == http_status.HTTP_405_METHOD_NOT_ALLOWED
    assert ManualReminder.objects.filter(pk=reminder.pk).exists()


def test_manual_patch_updates_title(client, staff):
    reminder = create_manual_reminder()
    response = client.patch(
        manual_detail_url(reminder.id),
        {"title": "Updated title"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == http_status.HTTP_200_OK
    assert response.data["title"] == "Updated title"
