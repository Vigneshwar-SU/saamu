"""Customer communication preparation for Phase 18.

A thin, read-only presentation layer over the existing authoritative customer,
order and payment services. All message wording, phone normalization and
WhatsApp handoff URL construction are centralized here so they are
deterministic and independently testable.

Data flow (Phase 18):
    authoritative data -> backend message preparation -> safe message payload
    -> the user chooses Copy or Open WhatsApp -> external WhatsApp handoff.

Safety rules honoured:
- No automatic sending, no provider credentials, no webhooks, no workers.
- Only the existing ``Customer.mobile_number`` is used; nothing is stored.
- Phone numbers are normalized conservatively and never logged.
- WhatsApp URLs use a fixed handoff base and a URL-encoded message; arbitrary
  URL input is never accepted.
- Messages never include internal notes, audit metadata or unrelated data and
  never claim a message was sent or delivered.
- Every financial value is taken verbatim from the backend services; the
  frontend never reconstructs totals or balances.
"""

import re
from decimal import Decimal
from urllib.parse import quote

from apps.billing.models import Invoice
from apps.billing.services import order_payment_summary, shop_details_data
from apps.orders.models import ALLOWED_TRANSITIONS, OrderStatus

WHATSAPP_BASE_URL = "https://wa.me/"

MESSAGE_TYPE_ORDER_ACKNOWLEDGEMENT = "ORDER_ACKNOWLEDGEMENT"
MESSAGE_TYPE_ORDER_STATUS_UPDATE = "ORDER_STATUS_UPDATE"
MESSAGE_TYPE_READY_FOR_COLLECTION = "READY_FOR_COLLECTION"
MESSAGE_TYPE_PAYMENT_BALANCE = "PAYMENT_BALANCE"

SUPPORTED_MESSAGE_TYPES = (
    MESSAGE_TYPE_ORDER_ACKNOWLEDGEMENT,
    MESSAGE_TYPE_ORDER_STATUS_UPDATE,
    MESSAGE_TYPE_READY_FOR_COLLECTION,
    MESSAGE_TYPE_PAYMENT_BALANCE,
)

# Formatting that is harmless to strip from a stored phone number.
_PHONE_FORMATTING_RE = re.compile(r"[\s\-()./]+")

# A bare 10-digit mobile whose first digit is 6-9 is unambiguously an Indian
# mobile in this India-only business (INR pricing, shop in Bengaluru), so the
# country code may be added without guessing.
_INDIA_MOBILE_PREFIXES = ("6", "7", "8", "9")
_INDIA_COUNTRY_CODE = "91"


def format_inr(amount):
    """Format a monetary amount as INR with Indian digit grouping.

    Deterministic and locale-independent (e.g. ``₹45,050.50``). Uses Decimal
    arithmetic only, so monetary values are always exact.
    """
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    sign = "-" if value < 0 else ""
    whole, _, fraction = format(abs(value), "f").partition(".")
    if len(whole) > 3:
        last_three = whole[-3:]
        head = whole[:-3]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        groups.insert(0, head)
        whole = ",".join(groups) + "," + last_three
    return f"{sign}₹{whole}.{fraction}"


def normalize_phone(value):
    """Return a WhatsApp-safe international number (digits only) or ``None``.

    Rules:
    - Harmless formatting (spaces, hyphens, dots, parentheses, slashes) is
      stripped.
    - A number with an explicit leading ``+`` and 7-15 digits is kept as-is;
      the country context is explicit and never guessed.
    - A bare 10-digit Indian mobile (first digit 6-9) is the only case where a
      country code is added: the business operates solely in India, so the
      context is unambiguous.
    - A trunk-prefixed Indian mobile (``0`` + 10 digits) is normalized the
      same way.
    - Any other value (empty, too short, ambiguous length, non-digits) is
      unusable and returns ``None``.
    """
    if value is None:
        return None
    cleaned = _PHONE_FORMATTING_RE.sub("", str(value).strip())
    if not cleaned:
        return None
    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if digits.isdigit() and 7 <= len(digits) <= 15:
            return digits
        return None
    if cleaned.isdigit():
        if len(cleaned) == 10 and cleaned[0] in _INDIA_MOBILE_PREFIXES:
            return _INDIA_COUNTRY_CODE + cleaned
        if (
            len(cleaned) == 11
            and cleaned[0] == "0"
            and cleaned[1] in _INDIA_MOBILE_PREFIXES
        ):
            return _INDIA_COUNTRY_CODE + cleaned[1:]
    return None


def build_whatsapp_url(destination, message):
    """Build the WhatsApp handoff URL from a validated destination and text.

    ``destination`` must come from ``normalize_phone`` (digits only); arbitrary
    URL input is never accepted because this function only ever receives the
    validated number. The message is URL-encoded (UTF-8) for the ``text``
    parameter.
    """
    if not destination or not str(destination).isdigit():
        return None
    encoded_message = quote(message, safe="")
    return f"{WHATSAPP_BASE_URL}{destination}?text={encoded_message}"


def _format_date(value):
    return value.strftime("%d %b %Y")


def _order_items_summary(order):
    """Concise, deterministic garment summary, e.g. ``2x Shirt, 1x Pant``."""
    items = list(order.items.order_by("id"))
    if not items:
        return None
    return ", ".join(
        f"{item.quantity}x {item.get_garment_type_display()}" for item in items
    )


def _next_step_label(status):
    """Authoritative next step label, or ``None`` when not determinable.

    The lifecycle (``ALLOWED_TRANSITIONS``) defines the possible forward steps;
    when exactly one non-cancelled step exists for the current status it is
    included, otherwise next-step information is omitted.
    """
    targets = ALLOWED_TRANSITIONS.get(status, set()) - {OrderStatus.CANCELLED}
    if len(targets) == 1:
        return OrderStatus(next(iter(targets))).label
    return None


def _sign_off(shop_name):
    return ["Regards,", shop_name]


def _build_acknowledgement(order, summary, shop):
    lines = [
        f"Hello {order.customer.full_name},",
        "",
        f"Thank you for your order at {shop['name']}.",
        "",
        f"Order Number: {order.order_number}",
        f"Order Date: {_format_date(order.order_date)}",
    ]
    items_summary = _order_items_summary(order)
    if items_summary:
        lines.append(f"Items: {items_summary}")
    lines.append(f"Total: {format_inr(order.total_amount)}")
    if summary["has_invoice"] or summary["total_paid"] > 0:
        lines.append(f"Amount Paid: {format_inr(summary['total_paid'])}")
        lines.append(f"Balance: {format_inr(summary['outstanding_balance'])}")
    if order.expected_delivery_date:
        lines.append(f"Expected Delivery: {_format_date(order.expected_delivery_date)}")
    lines.extend(
        [
            "",
            "We will update you when your order is ready for collection.",
            "",
        ]
    )
    lines.extend(_sign_off(shop["name"]))
    return "\n".join(lines)


def _build_status_update(order, summary, shop):
    lines = [
        f"Hello {order.customer.full_name},",
        "",
        "Update on your order.",
        "",
        f"Order Number: {order.order_number}",
        f"Current Status: {OrderStatus(order.status).label}",
    ]
    if order.expected_delivery_date:
        lines.append(f"Expected Delivery: {_format_date(order.expected_delivery_date)}")
    next_step = _next_step_label(order.status)
    if next_step:
        lines.append(f"Next Step: {next_step}.")
    lines.extend(["", ""])
    lines.extend(_sign_off(shop["name"]))
    return "\n".join(lines)


def _build_ready_for_collection(order, summary, shop):
    lines = [
        f"Hello {order.customer.full_name},",
        "",
        "Good news! Your order is ready for collection.",
        "",
        f"Order Number: {order.order_number}",
        "",
        f"Please collect it from {shop['name']}.",
    ]
    if shop["address"]:
        lines.append(f"Shop Address: {shop['address']}")
    if shop["phone"]:
        lines.append(f"Shop Phone: {shop['phone']}")
    lines.extend(["", ""])
    lines.extend(_sign_off(shop["name"]))
    return "\n".join(lines)


def _build_payment_balance(order, summary, shop):
    status_label = Invoice.Status(summary["payment_status"]).label
    lines = [
        f"Hello {order.customer.full_name},",
        "",
        "Payment summary for your order.",
        "",
        f"Order Number: {order.order_number}",
        f"Total: {format_inr(summary['order_total'])}",
        f"Amount Paid: {format_inr(summary['total_paid'])}",
        f"Balance: {format_inr(summary['outstanding_balance'])}",
        f"Payment Status: {status_label}",
        "",
    ]
    lines.extend(_sign_off(shop["name"]))
    return "\n".join(lines)


_MESSAGE_BUILDERS = {
    MESSAGE_TYPE_ORDER_ACKNOWLEDGEMENT: _build_acknowledgement,
    MESSAGE_TYPE_ORDER_STATUS_UPDATE: _build_status_update,
    MESSAGE_TYPE_READY_FOR_COLLECTION: _build_ready_for_collection,
    MESSAGE_TYPE_PAYMENT_BALANCE: _build_payment_balance,
}


def build_order_communication(order, message_type):
    """Prepare the communication payload for an order.

    Returns ``{message_type, message, phone_number, whatsapp_url}``. Only reads
    are performed: nothing is saved, sent or logged. ``message_type`` must be
    one of ``SUPPORTED_MESSAGE_TYPES``; anything else raises ``ValueError``.
    """
    if message_type not in SUPPORTED_MESSAGE_TYPES:
        raise ValueError(f"Unsupported message type: {message_type}")
    summary = order_payment_summary(order)
    shop = shop_details_data()
    message = _MESSAGE_BUILDERS[message_type](order, summary, shop)
    phone_number = normalize_phone(order.customer.mobile_number)
    return {
        "message_type": message_type,
        "message": message,
        "phone_number": phone_number,
        "whatsapp_url": build_whatsapp_url(phone_number, message),
    }
