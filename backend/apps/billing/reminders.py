"""Operational reminder preparation for Phase 19.

A thin, read-only orchestration layer over the existing authoritative order,
payment and communication services. Reminders are **derived, never stored**:
repeated evaluation of the same unchanged business state produces the same
candidate set, which is what makes the workflow idempotent without any new
persistence (and therefore without any migration).

Data flow:
    authoritative order/payment state -> eligibility evaluation
    -> deterministic reminder candidate -> Phase 18 message preparation
    -> operator review -> WhatsApp-ready handoff (copy or open).

The reminder set is deliberately small and justified purely by data that
already exists in the repository:

- ``READY_FOR_COLLECTION``: an active order whose status is READY. The message
  is the Phase 18 ready-for-collection template, which itself requires the
  order to actually be READY so it never makes an unsupported claim.
- ``BALANCE_OUTSTANDING``: an active order that has an invoice with an
  outstanding balance greater than zero. The message is the Phase 18
  payment/balance template. Orders without an invoice are never reminded: the
  authoritative payment summary reports no billable relationship yet, so a
  payment reminder would be premature.

Terminal orders (COLLECTED / CANCELLED) are never candidates: they are closed
lifecycle states, and a cancelled order with an outstanding balance is treated
as invalid business state rather than a reminder to chase.

Safety rules honoured (same as Phase 18):
- Nothing is ever sent, stored or logged; there are no mutation endpoints.
- ``Customer.mobile_number`` is the only phone source, normalized by Phase 18.
- The full phone number and WhatsApp URL appear only in the prepared payload,
  never in log statements.
- Every financial figure comes verbatim from ``order_payment_summary``.
"""

from apps.billing.communications import (
    MESSAGE_TYPE_PAYMENT_BALANCE,
    MESSAGE_TYPE_READY_FOR_COLLECTION,
    build_order_communication,
    format_inr,
)
from apps.billing.services import order_payment_summary
from apps.orders.models import TERMINAL_STATUSES, Order, OrderStatus

REMINDER_READY_FOR_COLLECTION = "READY_FOR_COLLECTION"
REMINDER_BALANCE_OUTSTANDING = "BALANCE_OUTSTANDING"

# The complete set of implemented reminder types. The ordering here is the
# deterministic sort order used by the pending-reminders list.
REMINDER_TYPES = (
    REMINDER_READY_FOR_COLLECTION,
    REMINDER_BALANCE_OUTSTANDING,
)

REMINDER_TYPE_LABELS = {
    REMINDER_READY_FOR_COLLECTION: "Ready for Collection",
    REMINDER_BALANCE_OUTSTANDING: "Balance Outstanding",
}

# Phase 18 message template used to prepare each reminder type. Wording,
# money formatting and WhatsApp URL construction stay in ``communications``.
REMINDER_MESSAGE_TYPES = {
    REMINDER_READY_FOR_COLLECTION: MESSAGE_TYPE_READY_FOR_COLLECTION,
    REMINDER_BALANCE_OUTSTANDING: MESSAGE_TYPE_PAYMENT_BALANCE,
}

# Stable eligibility codes exposed to operators (not invented per request).
# When a reminder is eligible its code is the reminder type itself.
REASON_ORDER_TERMINAL = "ORDER_TERMINAL"
REASON_ORDER_NOT_READY = "ORDER_NOT_READY"
REASON_NO_INVOICE = "NO_INVOICE"
REASON_NO_OUTSTANDING_BALANCE = "NO_OUTSTANDING_BALANCE"

_REMINDER_ID_SEPARATOR = "_"


class ReminderNotEligible(Exception):
    """Raised when a reminder is requested for an order that is not eligible."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def reminder_id(reminder_type, order_id):
    """Stable identifier for a derived reminder: ``<TYPE>_<order_id>``."""
    return f"{reminder_type}{_REMINDER_ID_SEPARATOR}{order_id}"


def parse_reminder_id(value):
    """Parse a reminder id into ``(reminder_type, order_id)`` or ``None``.

    The separator is split from the right so reminder types that themselves
    contain underscores (every implemented type does) are handled correctly.
    """
    if not isinstance(value, str) or _REMINDER_ID_SEPARATOR not in value:
        return None
    reminder_type, _, order_part = value.rpartition(_REMINDER_ID_SEPARATOR)
    if reminder_type not in REMINDER_TYPES or not order_part.isdigit():
        return None
    return reminder_type, int(order_part)


def _eligible_ready_for_collection(order):
    """Eligibility for the ready-for-collection reminder."""
    if order.status == OrderStatus.READY:
        return (
            True,
            REMINDER_READY_FOR_COLLECTION,
            ("The order is ready for collection."),
        )
    if order.status in TERMINAL_STATUSES:
        return False, REASON_ORDER_TERMINAL, "Terminal orders are not reminded."
    return (
        False,
        REASON_ORDER_NOT_READY,
        (f"The order is currently {order.get_status_display().lower()}."),
    )


def _eligible_balance_outstanding(order):
    """Eligibility for the balance-outstanding reminder.

    Uses the authoritative payment summary directly: an invoice must exist
    (a billable relationship) and the outstanding balance must be positive.
    """
    if order.status in TERMINAL_STATUSES:
        return False, REASON_ORDER_TERMINAL, "Terminal orders are not reminded."
    summary = order_payment_summary(order)
    if not summary["has_invoice"]:
        return False, REASON_NO_INVOICE, "The order has no invoice."
    if summary["outstanding_balance"] <= 0:
        return (
            False,
            REASON_NO_OUTSTANDING_BALANCE,
            ("The order has no outstanding balance."),
        )
    return (
        True,
        REMINDER_BALANCE_OUTSTANDING,
        (
            "An outstanding balance of "
            f"{format_inr(summary['outstanding_balance'])} remains."
        ),
    )


_ELIGIBILITY_EVALUATORS = {
    REMINDER_READY_FOR_COLLECTION: _eligible_ready_for_collection,
    REMINDER_BALANCE_OUTSTANDING: _eligible_balance_outstanding,
}


def evaluate_reminder_eligibility(order, reminder_type):
    """Return ``(eligible, code, message)`` for one reminder type on an order.

    ``code`` is the reminder type when eligible, otherwise one of the stable
    ``REASON_*`` codes. The result is a pure function of persisted state, so it
    is deterministic.
    """
    if reminder_type not in _ELIGIBILITY_EVALUATORS:
        raise ValueError(f"Unsupported reminder type: {reminder_type}")
    return _ELIGIBILITY_EVALUATORS[reminder_type](order)


def build_reminder_candidate(order, reminder_type):
    """Build a fully prepared reminder candidate for an order.

    Re-validates current eligibility and raises ``ReminderNotEligible`` when
    the reminder can no longer be prepared (the reminder is stale), so a
    reminder is never forced through inconsistent business state. The message
    is prepared by the Phase 18 ``build_order_communication`` and therefore
    agrees exactly with the authoritative payment summary.
    """
    eligible, code, message = evaluate_reminder_eligibility(order, reminder_type)
    if not eligible:
        raise ReminderNotEligible(code, message)
    prepared = build_order_communication(order, REMINDER_MESSAGE_TYPES[reminder_type])
    return {
        "id": reminder_id(reminder_type, order.id),
        "reminder_type": reminder_type,
        "reminder_type_label": REMINDER_TYPE_LABELS[reminder_type],
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
        },
        "customer": {
            "id": order.customer.id,
            "full_name": order.customer.full_name,
        },
        "eligibility": {
            "eligible": True,
            "code": code,
            "message": message,
        },
        "message": prepared["message"],
        "phone_number": prepared["phone_number"],
        "whatsapp_url": prepared["whatsapp_url"],
    }


def build_pending_reminders():
    """Return the deterministic set of currently eligible reminder candidates.

    Only active (non-terminal) orders are considered. Candidates are ordered by
    order id and then by the fixed ``REMINDER_TYPES`` order, so repeated calls
    on unchanged state return identical results (the idempotency guarantee -
    nothing is persisted, so nothing can be duplicated).
    """
    orders = (
        Order.objects.select_related("customer")
        .exclude(status__in=TERMINAL_STATUSES)
        .order_by("id")
    )
    candidates = []
    for order in orders:
        for reminder_type in REMINDER_TYPES:
            eligible, _code, _message = evaluate_reminder_eligibility(
                order, reminder_type
            )
            if eligible:
                candidates.append(build_reminder_candidate(order, reminder_type))
    return candidates
