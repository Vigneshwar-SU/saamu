"""Full Shirt / Half Shirt variant behaviour.

A shirt line is always a Full Shirt or a Half Shirt. The two variants:

* share ONE customer measurement chart (the plain ``SHIRT`` measurement),
* are priced independently by the customer on the order line,
* are paid to tailors under separate, configurable piece rates,
* appear as distinct labels on invoices, payroll and reports.

Historical shirt lines created before variants existed keep ``shirt_type =
NULL``. They are never silently reclassified as Full Shirt: they keep
resolving to the legacy ``SHIRT`` rate and display as a plain "Shirt".
"""

import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.billing.serializers import ManualReminderSerializer
from apps.orders.models import (
    PIECE_RATE_KEY_FULL_SHIRT,
    PIECE_RATE_KEY_HALF_SHIRT,
    GarmentType,
    Order,
    OrderItem,
    ShirtType,
)
from apps.orders.tests.helpers import (
    AUTO_SHIRT_TYPE,
    create_measurement,
    order_detail_url,
    order_item_payload,
    order_list_url,
    order_work_progress_url,
)
from apps.tailors.models import WorkAssignment
from apps.tailors.tests.helpers import (
    assign_payload,
    create_assignment,
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
    make_staff,
    work_assignments_url,
)
from apps.customers.tests.helpers import auth_header

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _create_order(client, staff, customer, items):
    return client.post(
        order_list_url(),
        {"customer": customer.id, "items": items},
        content_type="application/json",
        **_auth(staff),
    )


# ---------------------------------------------------------------------------
# A. Shirt type is required and validated
# ---------------------------------------------------------------------------


def test_shirt_line_requires_a_shirt_type(client, staff):
    """A SHIRT with no variant is rejected outright."""
    customer = create_customer()
    measurement = create_measurement(customer, garment_type="SHIRT")

    response = _create_order(
        client,
        staff,
        customer,
        [order_item_payload("SHIRT", shirt_type=None, measurement_id=measurement.id)],
    )

    assert response.status_code == 400
    details = response.json()["error"]["details"]
    assert "shirt_type" in details["items"][0]


def test_pant_line_rejects_a_shirt_type(client, staff):
    """A shirt variant on a pant is meaningless, so it is refused."""
    customer = create_customer()
    measurement = create_measurement(customer, garment_type="PANT")

    response = _create_order(
        client,
        staff,
        customer,
        [
            order_item_payload(
                "PANT", shirt_type=ShirtType.FULL, measurement_id=measurement.id
            )
        ],
    )

    assert response.status_code == 400
    details = response.json()["error"]["details"]
    assert "shirt_type" in details["items"][0]


@pytest.mark.parametrize("variant", [ShirtType.FULL, ShirtType.HALF])
def test_both_variants_can_be_ordered(client, staff, variant):
    customer = create_customer()
    measurement = create_measurement(customer, garment_type="SHIRT")

    response = _create_order(
        client,
        staff,
        customer,
        [order_item_payload("SHIRT", shirt_type=variant, measurement_id=measurement.id)],
    )

    assert response.status_code == 201, response.content
    item = response.json()["items"][0]
    assert item["shirt_type"] == variant
    assert item["garment_label"] == variant.label


def test_both_variants_can_appear_on_one_order(client, staff):
    """A single order can mix a Full Shirt, a Half Shirt and a Pant."""
    customer = create_customer()
    shirt = create_measurement(customer, garment_type="SHIRT")
    pant = create_measurement(customer, garment_type="PANT")

    response = _create_order(
        client,
        staff,
        customer,
        [
            order_item_payload("SHIRT", shirt_type=ShirtType.FULL, measurement_id=shirt.id),
            order_item_payload("SHIRT", shirt_type=ShirtType.HALF, measurement_id=shirt.id),
            order_item_payload("PANT", measurement_id=pant.id),
        ],
    )

    assert response.status_code == 201, response.content
    labels = [item["garment_label"] for item in response.json()["items"]]
    assert labels == ["Full Shirt", "Half Shirt", "Pant"]


# ---------------------------------------------------------------------------
# B. Both variants share ONE measurement chart
# ---------------------------------------------------------------------------


def test_both_variants_reuse_the_same_shirt_measurement(client, staff):
    """The variant must not fork the measurement chart."""
    customer = create_customer()
    measurement = create_measurement(customer, garment_type="SHIRT")

    response = _create_order(
        client,
        staff,
        customer,
        [
            order_item_payload("SHIRT", shirt_type=ShirtType.FULL, measurement_id=measurement.id),
            order_item_payload("SHIRT", shirt_type=ShirtType.HALF, measurement_id=measurement.id),
        ],
    )

    assert response.status_code == 201, response.content
    items = response.json()["items"]
    assert {item["measurement_id"] for item in items} == {measurement.id}
    assert {item["measurement_version"] for item in items} == {measurement.version}
    # Only one shirt measurement row exists in total.
    assert customer.measurements.filter(garment_type="SHIRT").count() == 1


def test_shirt_measurement_snapshot_is_preserved_per_variant(client, staff):
    """Snapshotting stays a per-order concern, independent of the variant."""
    customer = create_customer()
    measurement = create_measurement(customer, garment_type="SHIRT", shirt_length=31.5)

    response = _create_order(
        client,
        staff,
        customer,
        [order_item_payload("SHIRT", shirt_type=ShirtType.HALF, measurement_id=measurement.id)],
    )

    assert response.status_code == 201
    item = response.json()["items"][0]
    assert item["measurement_snapshot"]["shirt_length"] == 31.5


# ---------------------------------------------------------------------------
# C. Legacy shirt lines are preserved, never reclassified
# ---------------------------------------------------------------------------


def test_legacy_shirt_line_keeps_null_variant(client, staff):
    """Existing data must not be migrated to Full Shirt behind staff's back."""
    customer = create_customer()
    order = Order.objects.create(customer=customer)
    legacy = OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        quantity=2,
        unit_price=Decimal("160.00"),
    )

    assert legacy.shirt_type is None
    assert legacy.garment_label == "Shirt"
    assert legacy.piece_rate_key == "SHIRT"

    body = client.get(order_detail_url(order.id), **_auth(staff)).json()
    item = body["items"][0]
    assert item["shirt_type"] is None
    assert item["garment_label"] == "Shirt"


def test_legacy_shirt_line_still_uses_the_legacy_rate(client, staff):
    """A pre-variant line keeps paying the historical SHIRT rate."""
    customer = create_customer()
    order = Order.objects.create(customer=customer)
    legacy = OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        quantity=3,
        unit_price=Decimal("160.00"),
    )
    create_piece_rate(garment_type=PIECE_RATE_KEY_FULL_SHIRT, rate_per_piece="200.00")
    create_piece_rate(garment_type="SHIRT", rate_per_piece="160.00")

    response = client.post(
        work_assignments_url(),
        assign_payload(create_tailor(), order, legacy, assigned_quantity=1),
        content_type="application/json",
        **_auth(staff),
    )

    assert response.status_code == 201, response.content
    assert response.json()["rate_per_piece_snapshot"] == 160.0


# ---------------------------------------------------------------------------
# D. Each variant resolves to its own configurable rate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "variant,expected_key",
    [
        (ShirtType.FULL, PIECE_RATE_KEY_FULL_SHIRT),
        (ShirtType.HALF, PIECE_RATE_KEY_HALF_SHIRT),
    ],
)
def test_each_variant_uses_its_own_rate(client, staff, variant, expected_key):
    customer = create_customer()
    order = Order.objects.create(customer=customer)
    item = OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        shirt_type=variant,
        quantity=2,
        unit_price=Decimal("100.00"),
    )
    create_piece_rate(garment_type=expected_key, rate_per_piece="175.00")
    # A different variant's rate must not be picked up.
    other = (
        "SHIRT_HALF" if expected_key == PIECE_RATE_KEY_FULL_SHIRT else PIECE_RATE_KEY_FULL_SHIRT
    )
    create_piece_rate(garment_type=other, rate_per_piece="999.00")

    response = client.post(
        work_assignments_url(),
        assign_payload(create_tailor(), order, item, assigned_quantity=1),
        content_type="application/json",
        **_auth(staff),
    )

    assert response.status_code == 201, response.content
    assert response.json()["rate_per_piece_snapshot"] == 175.0


def test_missing_variant_rate_blocks_assignment(client, staff):
    """A variant with no configured rate cannot be assigned."""
    customer = create_customer()
    order = Order.objects.create(customer=customer)
    half = OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        shirt_type=ShirtType.HALF,
        quantity=2,
        unit_price=Decimal("100.00"),
    )
    create_piece_rate(garment_type=PIECE_RATE_KEY_FULL_SHIRT, rate_per_piece="175.00")

    response = client.post(
        work_assignments_url(),
        assign_payload(create_tailor(), order, half, assigned_quantity=1),
        content_type="application/json",
        **_auth(staff),
    )

    assert response.status_code == 400
    assert "piece rate" in response.json()["error"]["details"]["order_item"]


def test_earnings_separate_full_and_half(client, staff):
    """A tailor's earnings must not merge the two shirt variants."""
    customer = create_customer()
    order = Order.objects.create(customer=customer)
    full = OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        shirt_type=ShirtType.FULL,
        quantity=2,
        unit_price=Decimal("100.00"),
    )
    half = OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        shirt_type=ShirtType.HALF,
        quantity=2,
        unit_price=Decimal("100.00"),
    )
    create_piece_rate(garment_type=PIECE_RATE_KEY_FULL_SHIRT, rate_per_piece="200.00")
    create_piece_rate(garment_type=PIECE_RATE_KEY_HALF_SHIRT, rate_per_piece="100.00")

    tailor = create_tailor()
    create_assignment(
        tailor,
        full,
        assigned_quantity=2,
        completed_quantity=2,
        status=WorkAssignment.Status.COMPLETED,
        rate_per_piece_snapshot="200.00",
    )
    create_assignment(
        tailor,
        half,
        assigned_quantity=2,
        completed_quantity=2,
        status=WorkAssignment.Status.COMPLETED,
        rate_per_piece_snapshot="100.00",
    )

    response = client.get(f"/api/v1/tailors/{tailor.id}/earnings/", **_auth(staff))
    assert response.status_code == 200
    breakdown = {
        entry["garment_label"]: entry["earned_amount"]
        for entry in response.json()["garment_breakdown"]
    }
    assert breakdown == {"Full Shirt": 400.0, "Half Shirt": 200.0}
    assert response.json()["summary"]["total_earned"] == 600.0


# ---------------------------------------------------------------------------
# E. Payroll stays on the immutable rate snapshot
# ---------------------------------------------------------------------------


def test_payroll_snapshot_survives_a_later_rate_change(client, staff):
    """Historical payroll must not move when a rate is re-priced."""
    customer = create_customer()
    order = Order.objects.create(customer=customer)
    item = OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        shirt_type=ShirtType.FULL,
        quantity=2,
        unit_price=Decimal("100.00"),
    )
    create_piece_rate(garment_type=PIECE_RATE_KEY_FULL_SHIRT, rate_per_piece="150.00")

    response = client.post(
        work_assignments_url(),
        assign_payload(create_tailor(), order, item, assigned_quantity=2),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201, response.content
    assignment_id = response.json()["id"]
    assert response.json()["rate_per_piece_snapshot"] == 150.0

    from apps.tailors.models import PieceRate

    PieceRate.objects.filter(garment_type=PIECE_RATE_KEY_FULL_SHIRT).update(
        rate_per_piece=Decimal("500.00")
    )

    detail = client.get(f"/api/v1/work-assignments/{assignment_id}/", **_auth(staff))
    assert detail.status_code == 200
    assert detail.json()["rate_per_piece_snapshot"] == 150.0
    assert detail.json()["earned_amount"] == 0.0

    started = client.post(
        f"/api/v1/work-assignments/{assignment_id}/status/",
        {"status": "IN_PROGRESS"},
        content_type="application/json",
        **_auth(staff),
    )
    assert started.status_code == 200, started.content
    completed = client.post(
        f"/api/v1/work-assignments/{assignment_id}/status/",
        {"status": "COMPLETED", "completed_quantity": 2},
        content_type="application/json",
        **_auth(staff),
    )
    assert completed.status_code == 200, completed.content
    # 2 pieces at the ORIGINAL 150.00 snapshot, not the re-priced 500.00.
    final = client.get(f"/api/v1/work-assignments/{assignment_id}/", **_auth(staff))
    assert final.json()["rate_per_piece_snapshot"] == 150.0
    assert final.json()["earned_amount"] == 300.0


# ---------------------------------------------------------------------------
# F. Serialization exposes the variant everywhere staff read it
# ---------------------------------------------------------------------------


def test_order_detail_exposes_variant_fields(client, staff):
    customer = create_customer()
    measurement = create_measurement(customer, garment_type="SHIRT")
    _create_order(
        client,
        staff,
        customer,
        [order_item_payload("SHIRT", shirt_type=ShirtType.HALF, measurement_id=measurement.id)],
    )
    order = Order.objects.get(customer=customer)

    body = client.get(order_detail_url(order.id), **_auth(staff)).json()
    item = body["items"][0]
    assert item["garment_code"] == "SHIRT"
    assert item["shirt_type"] == "HALF"
    assert item["shirt_type_label"] == "Half Shirt"
    assert item["garment_label"] == "Half Shirt"

    summary = body["garment_summary"][0]
    assert summary["shirt_type"] == "HALF"
    assert summary["garment_label"] == "Half Shirt"


def test_work_progress_labels_each_variant(client, staff):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 1})
    full = get_order_item(order, "SHIRT")
    OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        shirt_type=ShirtType.HALF,
        quantity=1,
        unit_price=Decimal("100.00"),
    )

    body = client.get(order_work_progress_url(order.id), **_auth(staff)).json()
    labels = [item["garment_label"] for item in body["data"]["items"]]
    assert sorted(labels) == ["Full Shirt", "Half Shirt"]


def test_work_assignment_exposes_variant_and_customer_notes(client, staff):
    """Staff need both the variant and the internal customer note."""
    customer = create_customer(notes="Prefers morning pickup")
    order = create_order_with_items(customer, {"SHIRT": 1})
    item = get_order_item(order, "SHIRT")
    item.shirt_type = ShirtType.HALF
    item.save(update_fields=["shirt_type"])
    create_piece_rate(garment_type=PIECE_RATE_KEY_HALF_SHIRT, rate_per_piece="120.00")

    response = client.post(
        work_assignments_url(),
        assign_payload(create_tailor(), order, item, assigned_quantity=1),
        content_type="application/json",
        **_auth(staff),
    )

    assert response.status_code == 201, response.content
    order_item = response.json()["order_item"]
    assert order_item["garment_label"] == "Half Shirt"
    assert order_item["shirt_type"] == "HALF"
    assert order_item["customer_notes"] == "Prefers morning pickup"


def test_invoice_snapshots_the_variant_label(client, staff):
    """The invoice records the variant as it was at billing time."""
    customer = create_customer()
    order = Order.objects.create(customer=customer)
    OrderItem.objects.create(
        order=order,
        garment_type=GarmentType.SHIRT,
        shirt_type=ShirtType.HALF,
        quantity=2,
        unit_price=Decimal("100.00"),
    )

    created = client.post(
        f"/api/v1/orders/{order.id}/invoice/",
        {},
        content_type="application/json",
        **_auth(staff),
    )
    assert created.status_code == 201, created.content
    invoice_id = created.json()["invoice"]["id"]

    detail = client.get(f"/api/v1/invoices/{invoice_id}/", **_auth(staff))
    assert detail.status_code == 200
    assert detail.json()["items"][0]["garment_type"] == "Half Shirt"


def _reminder_candidates(client, staff):
    response = client.get("/api/v1/reminders/", **_auth(staff))
    assert response.status_code == 200
    return response.json()["data"]["results"]


def test_reminder_payload_carries_customer_notes_for_staff(client, staff):
    """Reminder cards are a staff surface, so notes ride along."""
    customer = create_customer(notes="Testing phase")
    Order.objects.create(
        customer=customer,
        status="NEW",
        expected_delivery_date=timezone.localdate() - timedelta(days=5),
    )

    candidates = _reminder_candidates(client, staff)
    payload = next(c for c in candidates if c["customer"]["id"] == customer.id)

    assert payload["customer"]["notes"] == "Testing phase"


def test_reminder_message_never_leaks_internal_notes(client, staff):
    """Internal notes are for staff eyes only, never the WhatsApp text.

    Uses a READY order because that reminder is the one that actually
    composes a customer-facing message.
    """
    customer = create_customer(notes="Testing phase")
    Order.objects.create(customer=customer, status="READY")

    candidates = _reminder_candidates(client, staff)
    payload = next(c for c in candidates if c["customer"]["id"] == customer.id)

    assert payload["message"]
    assert "Testing phase" not in payload["message"]
    assert "Testing phase" not in (payload.get("description") or "")
    assert "Testing phase" not in payload["title"]


def test_finance_income_exposes_customer_notes_for_staff(client, staff):
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

    body = client.get("/api/v1/income/", **_auth(staff))
    assert body.status_code == 200
    row = next(r for r in body.json()["results"] if r["id"] == payment.id)
    assert row["customer_notes"] == "created by integration check"


def test_manual_reminder_exposes_customer_notes_for_staff():
    from django.utils import timezone as _tz

    from apps.billing.models import ManualReminder

    customer = create_customer(notes="Prefers WhatsApp")
    reminder = ManualReminder.objects.create(
        title="Call back",
        reminder_date=_tz.localdate(),
        customer=customer,
        order=Order.objects.create(customer=customer),
    )

    data = ManualReminderSerializer(reminder).data

    assert data["customer"]["notes"] == "Prefers WhatsApp"


# ---------------------------------------------------------------------------
# G. Model-level invariants
# ---------------------------------------------------------------------------


def test_model_validation_requires_variant_for_new_shirt_lines():
    from django.core.exceptions import ValidationError

    customer = create_customer()
    order = Order.objects.create(customer=customer)
    item = OrderItem(order=order, garment_type=GarmentType.SHIRT, quantity=1)

    with pytest.raises(ValidationError):
        item.full_clean()


def test_model_validation_rejects_shirt_type_on_pant():
    from django.core.exceptions import ValidationError

    customer = create_customer()
    order = Order.objects.create(customer=customer)
    item = OrderItem(
        order=order,
        garment_type=GarmentType.PANT,
        shirt_type=ShirtType.FULL,
        quantity=1,
    )

    with pytest.raises(ValidationError):
        item.full_clean()


def test_piece_rate_key_mapping_is_exhaustive():
    assert (
        OrderItem(
            garment_type=GarmentType.SHIRT, shirt_type=ShirtType.FULL
        ).piece_rate_key
        == PIECE_RATE_KEY_FULL_SHIRT
    )
    assert (
        OrderItem(
            garment_type=GarmentType.SHIRT, shirt_type=ShirtType.HALF
        ).piece_rate_key
        == PIECE_RATE_KEY_HALF_SHIRT
    )
    assert OrderItem(garment_type=GarmentType.SHIRT).piece_rate_key == "SHIRT"
    assert OrderItem(garment_type=GarmentType.PANT).piece_rate_key == "PANT"
