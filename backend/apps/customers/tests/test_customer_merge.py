"""Tests for safe consolidation of duplicate customer records.

Covers the cleanup spec: detection by normalized mobile, canonical selection,
reassignment of every related record (orders, measurements, invoices,
payments, manual reminders), measurement version renumbering, deletion of the
duplicate only after relations move, preservation of financial history, and
that future duplicate creation remains rejected.
"""

from decimal import Decimal

import pytest

from apps.billing.models import CustomerPayment, Invoice, ManualReminder
from apps.customers.merge import (
    audit_database,
    choose_canonical,
    find_duplicate_groups,
    merge_customer,
    run_merge,
)
from apps.customers.models import Customer, Measurement
from apps.customers.tests.helpers import (
    create_customer,
    customer_list_url,
    make_staff,
    valid_customer_payload,
)
from apps.orders.models import Order
from apps.orders.tests.helpers import create_measurement

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(staff):
    from apps.authentication.tests.helpers import auth_header

    return {"HTTP_AUTHORIZATION": auth_header(staff)["HTTP_AUTHORIZATION"]}


def _create(client, staff, payload):
    return client.post(
        customer_list_url(), payload, content_type="application/json", **_auth(staff)
    )


def _payment(invoice, amount="150.00"):
    return CustomerPayment.objects.create(
        invoice=invoice,
        amount=Decimal(amount),
        payment_date="2026-08-01",
        payment_method=CustomerPayment.Method.CASH,
    )


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def test_duplicate_groups_detected_by_normalized_mobile():
    first = create_customer(full_name="A", mobile_number="9876543210")
    second = create_customer(full_name="B", mobile_number="+919876543210")
    third = create_customer(full_name="C", mobile_number="0 98765 43210")
    create_customer(full_name="Unique", mobile_number="9000000001")

    groups = find_duplicate_groups()

    assert "919876543210" in groups
    assert {c.id for c in groups["919876543210"]} == {first.id, second.id, third.id}
    assert len(groups) == 1


def test_different_mobile_formats_are_one_group():
    a = create_customer(full_name="A", mobile_number="9876543210")
    b = create_customer(full_name="B", mobile_number="+91 98765 43210")
    groups = find_duplicate_groups()
    assert {c.id for c in groups["919876543210"]} == {a.id, b.id}


# ---------------------------------------------------------------------------
# Canonical selection
# ---------------------------------------------------------------------------


def test_canonical_prefers_most_related_records():
    older = create_customer(full_name="Old", mobile_number="9876543210")
    newer = create_customer(full_name="New", mobile_number="+919876543210")
    Order.objects.create(customer=newer, total_amount=Decimal("100.00"))

    assert choose_canonical([older, newer]).id == newer.id


def test_canonical_tie_breaks_to_oldest():
    older = create_customer(full_name="Old", mobile_number="9876543210")
    newer = create_customer(full_name="New", mobile_number="+919876543210")

    assert choose_canonical([older, newer]).id == older.id


def test_canonical_keeps_its_primary_mobile():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    duplicate = create_customer(full_name="Ravi", mobile_number="+919876543210")

    run_merge()

    remaining = Customer.objects.get()
    assert remaining.id == canonical.id
    assert remaining.mobile_number == "9876543210"


# ---------------------------------------------------------------------------
# Reassignment (merge_customer moves duplicate -> canonical explicitly)
# ---------------------------------------------------------------------------


def test_merge_reassigns_orders():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    duplicate = create_customer(full_name="Ravi", mobile_number="+919876543210")
    order = Order.objects.create(customer=duplicate, total_amount=Decimal("100.00"))

    result = merge_customer(duplicate, canonical)

    assert result["deleted"] is True
    order.refresh_from_db()
    assert order.customer_id == canonical.id
    assert not Customer.objects.filter(pk=duplicate.pk).exists()


def test_merge_reassigns_manual_reminders():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    duplicate = create_customer(full_name="Ravi", mobile_number="+919876543210")
    reminder = ManualReminder.objects.create(
        customer=duplicate, title="Call customer", reminder_date="2026-08-15"
    )

    merge_customer(duplicate, canonical)

    reminder.refresh_from_db()
    assert reminder.customer_id == canonical.id


def test_merge_preserves_and_renumbers_measurements():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    duplicate = create_customer(full_name="Ravi", mobile_number="+919876543210")
    first = create_measurement(
        canonical, garment_type="SHIRT", version=1, is_current=True, neck_circumference=40
    )
    second = create_measurement(
        duplicate, garment_type="SHIRT", version=1, is_current=True, neck_circumference=41
    )

    merge_customer(duplicate, canonical)

    rows = Measurement.objects.filter(customer=canonical).order_by("version")
    assert [m.id for m in rows] == [first.id, second.id]
    assert [m.version for m in rows] == [1, 2]
    second.refresh_from_db()
    assert second.neck_circumference == Decimal("41.0")
    currents = Measurement.objects.filter(customer=canonical, is_current=True)
    assert [m.version for m in currents] == [2]


def test_merge_renumbers_multiple_duplicate_measurements_in_order():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    duplicate = create_customer(full_name="Ravi", mobile_number="+919876543210")
    create_measurement(canonical, garment_type="SHIRT", version=1, is_current=True)
    create_measurement(duplicate, garment_type="SHIRT", version=1, is_current=False)
    create_measurement(duplicate, garment_type="SHIRT", version=2, is_current=True)

    merge_customer(duplicate, canonical)

    rows = Measurement.objects.filter(customer=canonical).order_by("version")
    assert [m.version for m in rows] == [1, 2, 3]
    assert [m.is_current for m in rows] == [False, False, True]


def test_merge_preserves_invoices_and_payments():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    duplicate = create_customer(full_name="Ravi", mobile_number="+919876543210")
    order = Order.objects.create(customer=duplicate, total_amount=Decimal("150.00"))
    invoice = Invoice.objects.create(order=order)
    payment = _payment(invoice, "150.00")

    merge_customer(duplicate, canonical)

    order.refresh_from_db()
    assert order.customer_id == canonical.id
    invoice.refresh_from_db()
    assert invoice.order_id == order.id
    payment.refresh_from_db()
    assert payment.invoice_id == invoice.id
    assert payment.amount == Decimal("150.00")
    assert CustomerPayment.objects.count() == 1


def test_merge_does_not_lose_financial_history():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    duplicate = create_customer(full_name="Ravi", mobile_number="+919876543210")
    for customer in (canonical, duplicate):
        order = Order.objects.create(customer=customer, total_amount=Decimal("150.00"))
        invoice = Invoice.objects.create(order=order)
        _payment(invoice, "100.00")
        _payment(invoice, "50.00")

    before_orders = set(Order.objects.values_list("order_number", flat=True))
    before_invoices = set(Invoice.objects.values_list("invoice_number", flat=True))
    before_payment_ids = set(CustomerPayment.objects.values_list("id", flat=True))
    before_total = sum(CustomerPayment.objects.values_list("amount", flat=True))

    merge_customer(duplicate, canonical)

    assert set(Order.objects.values_list("order_number", flat=True)) == before_orders
    assert set(Invoice.objects.values_list("invoice_number", flat=True)) == before_invoices
    assert set(CustomerPayment.objects.values_list("id", flat=True)) == before_payment_ids
    assert sum(CustomerPayment.objects.values_list("amount", flat=True)) == before_total
    assert not Customer.objects.filter(pk=duplicate.pk).exists()


def test_duplicate_deleted_only_after_relations_reassigned():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    duplicate = create_customer(full_name="Ravi", mobile_number="+919876543210")
    order = Order.objects.create(customer=duplicate, total_amount=Decimal("100.00"))
    measurement = create_measurement(duplicate, garment_type="PANT", version=1)

    result = merge_customer(duplicate, canonical)

    assert result["deleted"] is True
    order.refresh_from_db()
    measurement.refresh_from_db()
    assert order.customer_id == canonical.id
    assert measurement.customer_id == canonical.id
    assert not Customer.objects.filter(pk=duplicate.pk).exists()


def test_run_merge_integration_consolidates_a_whole_group():
    oldest = create_customer(full_name="Ravi Kumar", mobile_number="9876543210")
    Order.objects.create(customer=oldest, total_amount=Decimal("100.00"))
    middle = create_customer(full_name="Ravi Kumar", mobile_number="+919876543210")
    order = Order.objects.create(customer=middle, total_amount=Decimal("50.00"))
    newest = create_customer(full_name="Ravi Kumar", mobile_number="0 98765 43210")

    results = run_merge()

    assert len(results) == 1
    assert results[0]["canonical_id"] == oldest.id
    assert len(results[0]["merges"]) == 2
    order.refresh_from_db()
    assert order.customer_id == oldest.id
    assert Customer.objects.count() == 1


def test_merge_profile_fills_missing_fields_without_overwriting():
    canonical = create_customer(
        full_name="Ravi Kumar",
        mobile_number="9876543210",
        address="12, MG Road, Bengaluru",
    )
    duplicate = create_customer(
        full_name="Ravi Kumar",
        mobile_number="+919876543210",
        notes="Prefers morning stitching",
    )

    run_merge()

    remaining = Customer.objects.get()
    assert remaining.full_name == "Ravi Kumar"
    assert remaining.address == "12, MG Road, Bengaluru"
    assert remaining.notes == "Prefers morning stitching"


def test_merge_reports_conflicting_profile_values():
    canonical = create_customer(
        full_name="Ravi Kumar", mobile_number="9876543210", notes="Canonical notes"
    )
    duplicate = create_customer(
        full_name="Ravi Kumar", mobile_number="+919876543210", notes="Duplicate notes"
    )

    result = merge_customer(duplicate, canonical)

    conflicts = result["profile"]["conflicts"]
    assert any(c["field"] == "notes" for c in conflicts)
    assert Customer.objects.get().notes == "Canonical notes"


def test_merge_does_not_import_conflicting_alternate():
    canonical = create_customer(full_name="Ravi", mobile_number="9876543210")
    other = create_customer(full_name="Other", mobile_number="9000000001")
    duplicate = create_customer(
        full_name="Ravi",
        mobile_number="+919876543210",
        alternate_mobile_number="9000000001",
    )

    run_merge()

    remaining = Customer.objects.get(full_name="Ravi")
    assert remaining.alternate_mobile_number == ""


def test_run_merge_with_no_duplicates_is_noop():
    create_customer(full_name="A", mobile_number="9876543210")
    create_customer(full_name="B", mobile_number="9000000001")
    assert run_merge() == []


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def test_audit_database_after_merge_reports_zero_duplicates():
    create_customer(full_name="A", mobile_number="9876543210")
    create_customer(full_name="B", mobile_number="+919876543210")

    run_merge()
    audit = audit_database()

    assert audit["total_customers"] == 1
    assert audit["unique_normalized_primaries"] == 1
    assert audit["duplicate_normalized_primaries"] == 0
    assert audit["duplicate_keys"] == {}


# ---------------------------------------------------------------------------
# Future duplicate prevention (API layer)
# ---------------------------------------------------------------------------


def test_after_merge_creating_same_mobile_is_rejected(client, staff):
    create_customer(full_name="A", mobile_number="9876543210")
    create_customer(full_name="B", mobile_number="+919876543210")
    run_merge()

    response = _create(client, staff, valid_customer_payload())
    assert response.status_code == 400
    assert "mobile_number" in response.json()["error"]["details"]


def test_customer_list_has_no_duplicate_normalized_mobiles_after_merge(client, staff):
    for index in range(9):
        create_customer(full_name="Ravi Kumar", mobile_number=f"900000{index:04d}")
    create_customer(full_name="Dup A", mobile_number="9876543210")
    create_customer(full_name="Dup B", mobile_number="+919876543210")

    run_merge()

    all_customers = []
    url = f"{customer_list_url()}?status=all"
    while url:
        response = client.get(url, **_auth(staff))
        assert response.status_code == 200
        data = response.json()
        all_customers.extend(data["results"])
        url = data["next"]
        if url:
            url = url.replace("http://testserver", "")

    assert len(all_customers) == 10
    from apps.customers.serializers import normalize_mobile_number

    normalized = [normalize_mobile_number(item["mobile_number"]) for item in all_customers]
    assert len(normalized) == len(set(normalized))
