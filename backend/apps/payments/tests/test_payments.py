"""Payroll payment API tests: finalized-only, overpayment and settlement flow."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.customers.tests.helpers import auth_header
from apps.payments.models import PayrollPayment
from apps.payments.tests.helpers import (
    create_finalized_entry,
    create_payment,
    entry_payments_url,
    entry_settlement_url,
    make_owner,
    make_staff,
)
from apps.payroll.models import PayrollPeriod
from apps.payroll.tests.helpers import (
    create_completed_assignment,
    create_payroll_period,
)
from apps.tailors.tests.helpers import (
    create_customer,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
)

pytestmark = pytest.mark.django_db

TODAY = date.today()


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


@pytest.fixture
def finalized_entry():
    return create_finalized_entry()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _payment_payload(amount="300.00", **extra):
    payload = {
        "amount": amount,
        "payment_date": str(TODAY),
        "payment_method": "CASH",
        "reference": "",
        "notes": "",
    }
    payload.update(extra)
    return payload


def test_anonymous_denied(client, finalized_entry):
    assert client.get(entry_payments_url(finalized_entry.id)).status_code == 401
    assert (
        client.post(
            entry_payments_url(finalized_entry.id),
            _payment_payload(),
            content_type="application/json",
        ).status_code
        == 401
    )


def test_owner_can_read_payment_history(client, owner, finalized_entry):
    create_payment(finalized_entry, amount="300.00")
    create_payment(finalized_entry, amount="200.00")

    response = client.get(entry_payments_url(finalized_entry.id), **_auth(owner))
    assert response.status_code == 200
    data = response.json()
    assert data["entry_id"] == finalized_entry.id
    assert len(data["payments"]) == 2
    assert data["payments"][0]["tailor"]["id"] == finalized_entry.tailor.id

    response = client.get(entry_settlement_url(finalized_entry.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["settlement"]["payments_recorded"] == 500.0


def test_owner_cannot_record_payment(client, owner, finalized_entry):
    response = client.post(
        entry_payments_url(finalized_entry.id),
        _payment_payload(),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_payment_requires_finalized_period(client, staff):
    tailor = create_tailor()
    period = create_payroll_period(status=PayrollPeriod.Status.CALCULATED)
    entry = period.entries.create(tailor=tailor, total_payable=Decimal("750.00"))

    response = client.post(
        entry_payments_url(entry.id),
        _payment_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "finalized" in response.json()["error"]["message"].lower()


def test_positive_amount_required(client, staff, finalized_entry):
    for amount in ("0", "-5", "0.00"):
        response = client.post(
            entry_payments_url(finalized_entry.id),
            _payment_payload(amount=amount),
            content_type="application/json",
            **_auth(staff),
        )
        assert response.status_code == 400, amount


def test_overpayment_rejected(client, staff, finalized_entry):
    response = client.post(
        entry_payments_url(finalized_entry.id),
        _payment_payload(amount="800.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "outstanding" in response.json()["error"]["message"].lower()

    assert PayrollPayment.objects.filter(payroll_entry=finalized_entry).count() == 0


def test_recorded_payment_tailor_matches_entry(client, staff, finalized_entry):
    response = client.post(
        entry_payments_url(finalized_entry.id),
        _payment_payload(amount="300.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    payment = PayrollPayment.objects.get(pk=response.json()["payment"]["id"])
    assert payment.tailor_id == finalized_entry.tailor_id


def test_multiple_partial_payments(client, staff, finalized_entry):
    response = client.post(
        entry_payments_url(finalized_entry.id),
        _payment_payload(amount="300.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    settlement = response.json()["settlement"]
    assert settlement["payments_recorded"] == 300.0
    assert settlement["outstanding_payable"] == 450.0
    assert settlement["settlement_status"] == "PARTIALLY_PAID"

    response = client.post(
        entry_payments_url(finalized_entry.id),
        _payment_payload(amount="250.00"),
        content_type="application/json",
        **_auth(staff),
    )
    settlement = response.json()["settlement"]
    assert settlement["payments_recorded"] == 550.0
    assert settlement["outstanding_payable"] == 200.0


def test_exact_final_payment_settles(client, staff, finalized_entry):
    response = client.post(
        entry_payments_url(finalized_entry.id),
        _payment_payload(amount="750.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    settlement = response.json()["settlement"]
    assert settlement["outstanding_payable"] == 0.0
    assert settlement["settlement_status"] == "SETTLED"


def test_decimal_arithmetic_is_exact(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = create_order_with_items(customer, {"SHIRT": 10})
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.25")
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 5, 5, "150.25", timezone.now())
    period.calculate()
    period.status = PayrollPeriod.Status.FINALIZED
    period.save(update_fields=["status", "updated_at"])
    entry = period.entries.get(tailor=tailor)

    # 5 pieces x 150.25 = 751.25 exact.
    assert entry.total_payable == Decimal("751.25")

    response = client.post(
        entry_payments_url(entry.id),
        _payment_payload(amount="300.15"),
        content_type="application/json",
        **_auth(staff),
    )
    settlement = response.json()["settlement"]
    assert settlement["payments_recorded"] == 300.15
    assert settlement["outstanding_payable"] == 451.10


def test_payment_history_preserved(client, staff, finalized_entry):
    for amount in ("300.00", "200.00", "250.00"):
        client.post(
            entry_payments_url(finalized_entry.id),
            _payment_payload(amount=amount),
            content_type="application/json",
            **_auth(staff),
        )

    response = client.get(entry_payments_url(finalized_entry.id), **_auth(staff))
    assert response.status_code == 200
    amounts = [p["amount"] for p in response.json()["payments"]]
    assert amounts == [250.0, 200.0, 300.0]  # newest first
    assert PayrollPayment.objects.filter(payroll_entry=finalized_entry).count() == 3


def test_entries_list_exposes_settlement(client, staff, finalized_entry):
    create_payment(finalized_entry, amount="300.00")
    response = client.get(
        "/api/v1/payroll/entries/?period=" f"{finalized_entry.payroll_period_id}",
        **_auth(staff),
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    settlement = results[0]["settlement"]
    assert settlement["gross_payable"] == 750.0
    assert settlement["payments_recorded"] == 300.0
    assert settlement["outstanding_payable"] == 450.0
