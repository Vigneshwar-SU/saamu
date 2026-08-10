"""Reminders V1 derivation service.

Reminders V1 surfaces actionable follow-ups across the existing authoritative
business data. Automatic reminders are **derived, never stored**: repeated
evaluation of the same unchanged state produces the same candidate set, so the
module needs no persistence of its own and never drifts out of sync. Only
``ManualReminder`` rows are persisted, and only for follow-ups the automatic
rules cannot express.

Reminder types (category in parentheses):

- ``OVERDUE_ORDER`` (orders): an active order whose expected delivery date is
  in the past.
- ``ORDER_DUE_TODAY`` (orders): an active order due today.
- ``ORDER_DUE_TOMORROW`` (orders): an active order due tomorrow.
- ``READY_FOR_PICKUP`` (orders): an active order that is READY. Reuses the
  Phase 18 ready-for-collection message for the WhatsApp action.
- ``PAYMENT_OUTSTANDING`` (payments): an active order with an invoice whose
  outstanding balance is positive. Uses the authoritative payment summary.
- ``TAILOR_WORKLOAD`` (tailors): one reminder per active tailor with unfinished
  assigned pieces (outstanding = assigned - completed > 0), with the related
  order context.
- ``MEASUREMENT_MISSING`` (orders): an active order item whose measurement
  reference is missing or whose snapshot lacks a required garment value.
- ``CUSTOMER_FOLLOW_UP`` (customers): an active customer whose latest order
  is older than the configured inactivity threshold (months).
- ``MANUAL_REMINDER`` (manual): a persisted PENDING ``ManualReminder`` row.

Safety rules (inherited from Phase 18/19): nothing is ever sent, stored or
logged; WhatsApp messages appear only in the prepared payload; every financial
figure comes verbatim from ``order_payment_summary``.
"""

import calendar
from datetime import date as date_cls
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Max
from django.utils import timezone

from apps.billing.communications import (
    MESSAGE_TYPE_PAYMENT_BALANCE,
    MESSAGE_TYPE_READY_FOR_COLLECTION,
    build_order_communication,
)
from apps.billing.models import ManualReminder, ShopDetails
from apps.billing.services import order_payment_summary
from apps.customers.models import GARMENT_REQUIRED_FIELDS, Customer
from apps.orders.models import TERMINAL_STATUSES, Order, OrderItem, OrderStatus
from apps.tailors.models import WorkAssignment

REMINDER_OVERDUE_ORDER = "OVERDUE_ORDER"
REMINDER_ORDER_DUE_TODAY = "ORDER_DUE_TODAY"
REMINDER_ORDER_DUE_TOMORROW = "ORDER_DUE_TOMORROW"
REMINDER_READY_FOR_PICKUP = "READY_FOR_PICKUP"
REMINDER_PAYMENT_OUTSTANDING = "PAYMENT_OUTSTANDING"
REMINDER_TAILOR_WORKLOAD = "TAILOR_WORKLOAD"
REMINDER_MEASUREMENT_MISSING = "MEASUREMENT_MISSING"
REMINDER_CUSTOMER_FOLLOW_UP = "CUSTOMER_FOLLOW_UP"
REMINDER_MANUAL = "MANUAL_REMINDER"

REMINDER_TYPES = (
    REMINDER_OVERDUE_ORDER,
    REMINDER_ORDER_DUE_TODAY,
    REMINDER_ORDER_DUE_TOMORROW,
    REMINDER_READY_FOR_PICKUP,
    REMINDER_PAYMENT_OUTSTANDING,
    REMINDER_TAILOR_WORKLOAD,
    REMINDER_MEASUREMENT_MISSING,
    REMINDER_CUSTOMER_FOLLOW_UP,
    REMINDER_MANUAL,
)

REMINDER_TYPE_LABELS = {
    REMINDER_OVERDUE_ORDER: "Overdue Order",
    REMINDER_ORDER_DUE_TODAY: "Order Due Today",
    REMINDER_ORDER_DUE_TOMORROW: "Order Due Tomorrow",
    REMINDER_READY_FOR_PICKUP: "Ready for Pickup",
    REMINDER_PAYMENT_OUTSTANDING: "Payment Outstanding",
    REMINDER_TAILOR_WORKLOAD: "Tailor Workload",
    REMINDER_MEASUREMENT_MISSING: "Measurement Missing",
    REMINDER_CUSTOMER_FOLLOW_UP: "Customer Follow-up",
    REMINDER_MANUAL: "Manual Reminder",
}

CATEGORY_ORDERS = "orders"
CATEGORY_PAYMENTS = "payments"
CATEGORY_TAILORS = "tailors"
CATEGORY_CUSTOMERS = "customers"
CATEGORY_MANUAL = "manual"

REMINDER_CATEGORIES = {
    REMINDER_OVERDUE_ORDER: CATEGORY_ORDERS,
    REMINDER_ORDER_DUE_TODAY: CATEGORY_ORDERS,
    REMINDER_ORDER_DUE_TOMORROW: CATEGORY_ORDERS,
    REMINDER_READY_FOR_PICKUP: CATEGORY_ORDERS,
    REMINDER_PAYMENT_OUTSTANDING: CATEGORY_PAYMENTS,
    REMINDER_TAILOR_WORKLOAD: CATEGORY_TAILORS,
    REMINDER_MEASUREMENT_MISSING: CATEGORY_ORDERS,
    REMINDER_CUSTOMER_FOLLOW_UP: CATEGORY_CUSTOMERS,
    REMINDER_MANUAL: CATEGORY_MANUAL,
}

# Phase 18 message template used to prepare WhatsApp actions per reminder type.
# Wording, money formatting and WhatsApp URL construction stay in
# ``communications``; reminders with no WhatsApp action map to ``None``.
REMINDER_MESSAGE_TYPES = {
    REMINDER_READY_FOR_PICKUP: MESSAGE_TYPE_READY_FOR_COLLECTION,
    REMINDER_PAYMENT_OUTSTANDING: MESSAGE_TYPE_PAYMENT_BALANCE,
}

_MAX_DATE = date_cls.max


def _days_from_today(date_value):
    """Whole days between today and ``date_value`` (positive = overdue)."""
    return (date_cls.today() - date_value).days


def _add_months(value, months):
    """Return ``value`` shifted by ``months`` (negative shifts backwards)."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _order_payload(order):
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "status_label": order.get_status_display(),
        "expected_delivery_date": order.expected_delivery_date,
    }


def _customer_payload(customer):
    return {
        "id": customer.id,
        "full_name": customer.full_name,
    }


def _tailor_payload(tailor, outstanding):
    return {
        "id": tailor.id,
        "full_name": tailor.full_name,
        "outstanding_quantity": outstanding,
    }


def _action(kind, target_id, label):
    return {"kind": kind, "target_id": target_id, "label": label}


def _base_candidate(reminder_type, *, order=None, customer=None, tailor=None):
    """Shared candidate scaffold with the deterministic common fields."""
    return {
        "id": None,
        "reminder_type": reminder_type,
        "reminder_type_label": REMINDER_TYPE_LABELS[reminder_type],
        "category": REMINDER_CATEGORIES[reminder_type],
        "date": None,
        "priority": None,
        "title": None,
        "description": None,
        "order": _order_payload(order) if order is not None else None,
        "customer": _customer_payload(customer) if customer is not None else None,
        "tailor": tailor,
        "action": None,
        "message": None,
        "phone_number": None,
        "whatsapp_url": None,
        "is_manual": False,
    }


def _prepare_whatsapp(candidate, order, message_type):
    """Attach the prepared WhatsApp action payload to an order reminder."""
    prepared = build_order_communication(order, message_type)
    candidate["message"] = prepared["message"]
    candidate["phone_number"] = prepared["phone_number"]
    candidate["whatsapp_url"] = prepared["whatsapp_url"]


def _order_candidates(order, today):
    """Build the order-scoped reminders for one active order."""
    candidates = []
    due = order.expected_delivery_date

    if due and due < today:
        candidate = _base_candidate(
            REMINDER_OVERDUE_ORDER, order=order, customer=order.customer
        )
        candidate["id"] = f"{REMINDER_OVERDUE_ORDER}_{order.id}"
        candidate["date"] = due
        candidate["title"] = f"Order {order.order_number} is overdue"
        candidate["description"] = (
            f"Expected delivery was {due} ({_days_from_today(due)} day(s) ago)."
        )
        candidate["action"] = _action("order", order.id, "View Order")
        candidates.append(candidate)

    if due == today:
        candidate = _base_candidate(
            REMINDER_ORDER_DUE_TODAY, order=order, customer=order.customer
        )
        candidate["id"] = f"{REMINDER_ORDER_DUE_TODAY}_{order.id}"
        candidate["date"] = today
        candidate["title"] = f"Order {order.order_number} is due today"
        candidate["description"] = "Expected delivery date is today."
        candidate["action"] = _action("order", order.id, "View Order")
        candidates.append(candidate)

    if due == today + timedelta(days=1):
        candidate = _base_candidate(
            REMINDER_ORDER_DUE_TOMORROW, order=order, customer=order.customer
        )
        candidate["id"] = f"{REMINDER_ORDER_DUE_TOMORROW}_{order.id}"
        candidate["date"] = due
        candidate["title"] = f"Order {order.order_number} is due tomorrow"
        candidate["description"] = "Expected delivery date is tomorrow."
        candidate["action"] = _action("order", order.id, "View Order")
        candidates.append(candidate)

    if order.status == OrderStatus.READY:
        candidate = _base_candidate(
            REMINDER_READY_FOR_PICKUP, order=order, customer=order.customer
        )
        candidate["id"] = f"{REMINDER_READY_FOR_PICKUP}_{order.id}"
        candidate["date"] = None
        candidate["title"] = f"Order {order.order_number} is ready for pickup"
        candidate["description"] = "The order is ready. Notify the customer."
        candidate["action"] = _action("order", order.id, "View Order")
        _prepare_whatsapp(candidate, order, MESSAGE_TYPE_READY_FOR_COLLECTION)
        candidates.append(candidate)

    return candidates


def _payment_candidates(order):
    """Build the payment-outstanding reminder when an invoice balance remains."""
    summary = order_payment_summary(order)
    if not summary["has_invoice"] or summary["outstanding_balance"] <= 0:
        return []
    candidate = _base_candidate(
        REMINDER_PAYMENT_OUTSTANDING, order=order, customer=order.customer
    )
    candidate["id"] = f"{REMINDER_PAYMENT_OUTSTANDING}_{order.id}"
    candidate["date"] = None
    candidate["title"] = f"Balance outstanding on {order.order_number}"
    candidate["description"] = (
        "An outstanding balance of "
        f"{summary['outstanding_balance']} remains on the invoice."
    )
    candidate["action"] = _action("order", order.id, "View Order")
    _prepare_whatsapp(candidate, order, MESSAGE_TYPE_PAYMENT_BALANCE)
    return [candidate]


def _tailor_workload_candidates():
    """One reminder per active tailor with unfinished assigned work."""
    assignments = (
        WorkAssignment.objects.select_related(
            "tailor", "order_item", "order_item__order"
        )
        .filter(tailor__is_active=True)
        .exclude(status=WorkAssignment.Status.COMPLETED)
        .order_by("tailor_id", "-assigned_at")
    )

    by_tailor = {}
    order_ids = set()
    for assignment in assignments:
        outstanding = assignment.assigned_quantity - assignment.completed_quantity
        if outstanding <= 0:
            continue
        entry = by_tailor.setdefault(
            assignment.tailor_id,
            {
                "tailor": assignment.tailor,
                "outstanding": 0,
                "orders": set(),
                "latest_order": None,
            },
        )
        entry["outstanding"] += outstanding
        order_id = assignment.order_item.order_id
        entry["orders"].add(order_id)
        if entry["latest_order"] is None:
            entry["latest_order"] = assignment.order_item.order
        order_ids.add(order_id)

    order_numbers = dict(
        Order.objects.filter(pk__in=order_ids).values_list("pk", "order_number")
    )

    candidates = []
    for entry in by_tailor.values():
        tailor = entry["tailor"]
        candidate = _base_candidate(
            REMINDER_TAILOR_WORKLOAD,
            order=entry["latest_order"],
            tailor=_tailor_payload(tailor, entry["outstanding"]),
        )
        candidate["id"] = f"{REMINDER_TAILOR_WORKLOAD}_{tailor.id}"
        candidate["date"] = None
        candidate["title"] = f"{tailor.full_name} has pending work"
        order_labels = ", ".join(order_numbers[oid] for oid in sorted(entry["orders"]))
        candidate["description"] = (
            f"{entry['outstanding']} piece(s) outstanding "
            f"across {len(entry['orders'])} order(s): {order_labels}."
        )
        candidate["action"] = _action("tailor", tailor.id, "View Tailor")
        candidates.append(candidate)
    return candidates


def _measurement_missing_candidates():
    """Items on active orders whose measurement reference or snapshot is missing."""
    items = (
        OrderItem.objects.select_related("order__customer")
        .exclude(order__status__in=TERMINAL_STATUSES)
        .order_by("id")
    )
    candidates = []
    for item in items:
        snapshot = item.measurement_snapshot or {}
        missing = [
            field_name
            for field_name in GARMENT_REQUIRED_FIELDS[item.garment_type]
            if snapshot.get(field_name) is None
        ]
        if item.measurement_id is None:
            missing_label = "no measurement reference"
        else:
            missing_label = ", ".join(missing) if missing else ""
        if not missing and item.measurement_id is not None:
            continue
        order = item.order
        candidate = _base_candidate(
            REMINDER_MEASUREMENT_MISSING, order=order, customer=order.customer
        )
        candidate["id"] = f"{REMINDER_MEASUREMENT_MISSING}_{item.id}"
        candidate["date"] = None
        candidate["title"] = f"Missing measurements on {order.order_number}"
        candidate["description"] = (
            f"{item.get_garment_type_display()} item is missing "
            f"measurement data: {missing_label or 'incomplete snapshot'}."
        )
        candidate["action"] = _action("order", order.id, "View Order")
        candidates.append(candidate)
    return candidates


def _customer_follow_up_candidates():
    """Active customers inactive for longer than the configured threshold."""
    threshold = ShopDetails.shop_details().customer_follow_up_months
    today = timezone.localdate()
    cutoff = _add_months(today, -threshold)

    rows = (
        Order.objects.filter(customer__is_active=True)
        .values("customer_id")
        .annotate(last_order_date=Max("order_date"), order_count=Count("id"))
        .filter(last_order_date__lt=cutoff)
    )
    if not rows:
        return []

    customers = {
        c.id: c
        for c in Customer.objects.filter(pk__in=[r["customer_id"] for r in rows])
    }
    latest_by_customer = {}
    latest_orders = (
        Order.objects.filter(customer_id__in=customers.keys())
        .select_related("customer")
        .order_by("customer_id", "-order_date")
    )
    for order in latest_orders:
        latest_by_customer.setdefault(order.customer_id, order)

    candidates = []
    for row in rows:
        customer = customers.get(row["customer_id"])
        if customer is None:
            continue
        last_order = latest_by_customer.get(row["customer_id"])
        last_order_date = row["last_order_date"]
        candidate = _base_candidate(REMINDER_CUSTOMER_FOLLOW_UP, customer=customer)
        candidate["id"] = f"{REMINDER_CUSTOMER_FOLLOW_UP}_{customer.id}"
        candidate["date"] = last_order_date
        candidate["title"] = f"Follow up with {customer.full_name}"
        candidate["description"] = (
            f"Last order was on {last_order_date} "
            f"({_days_from_today(last_order_date)} day(s) ago). "
            f"{row['order_count']} order(s) on record. "
            f"Follow-up threshold: {threshold} month(s) of inactivity."
        )
        candidate["order"] = (
            _order_payload(last_order) if last_order is not None else None
        )
        candidate["action"] = _action("customer", customer.id, "View Customer")
        candidates.append(candidate)
    return candidates


def _manual_candidates():
    """Persisted PENDING manual reminders, ready for operator action."""
    reminders = (
        ManualReminder.objects.filter(status=ManualReminder.Status.PENDING)
        .select_related("customer", "order")
        .order_by("reminder_date", "id")
    )
    candidates = []
    for reminder in reminders:
        candidate = _base_candidate(
            REMINDER_MANUAL,
            order=reminder.order if reminder.order_id else None,
            customer=reminder.customer if reminder.customer_id else None,
        )
        candidate["id"] = f"{REMINDER_MANUAL}_{reminder.id}"
        candidate["date"] = reminder.reminder_date
        candidate["priority"] = reminder.priority
        candidate["title"] = reminder.title
        candidate["description"] = reminder.description or ""
        candidate["action"] = _action("manual", reminder.id, "View Reminder")
        candidate["is_manual"] = True
        candidates.append(candidate)
    return candidates


def build_pending_reminder_candidates():
    """Return the deterministic set of all currently eligible reminders.

    Candidates are ordered by their ``date`` (dated reminders first, then the
    rest) and then by id, so repeated calls on unchanged state return identical
    results.
    """
    today = timezone.localdate()
    candidates = []
    for order in (
        Order.objects.select_related("customer")
        .exclude(status__in=TERMINAL_STATUSES)
        .order_by("id")
    ):
        candidates.extend(_order_candidates(order, today))
        candidates.extend(_payment_candidates(order))
    candidates.extend(_tailor_workload_candidates())
    candidates.extend(_measurement_missing_candidates())
    candidates.extend(_customer_follow_up_candidates())
    candidates.extend(_manual_candidates())

    def sort_key(candidate):
        return (
            candidate["date"] is None,
            candidate["date"] or _MAX_DATE,
            candidate["id"] or "",
        )

    return sorted(candidates, key=sort_key)


def reminder_summary():
    """Counts of the currently eligible reminders per type and category."""
    candidates = build_pending_reminder_candidates()
    by_type = {reminder_type: 0 for reminder_type in REMINDER_TYPES}
    by_category = {category: 0 for category in REMINDER_CATEGORIES.values()}
    for candidate in candidates:
        by_type[candidate["reminder_type"]] += 1
        by_category[candidate["category"]] += 1
    return {
        "total": len(candidates),
        "by_type": by_type,
        "by_category": by_category,
    }
