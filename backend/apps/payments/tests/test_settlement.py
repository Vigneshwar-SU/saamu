"""Payroll settlement tests: derived values, advance deduction and concurrency."""

from datetime import date
from decimal import Decimal

import pytest

from apps.customers.tests.helpers import auth_header
from apps.payments.models import PayrollPayment, SalaryAdvance
from apps.payments.services import (
    apply_advance,
    outstanding_payable,
    period_settlement_summary,
    record_payment,
    settlement_summary,
)
from apps.payments.tests.helpers import (
    create_advance,
    create_finalized_entry,
    create_payment,
    entry_apply_advance_url,
    entry_payments_url,
    entry_settle_url,
    entry_settlement_url,
    make_owner,
    make_staff,
)
from apps.payroll.models import PayrollEntry, PayrollPeriod
from apps.payroll.tests.helpers import create_payroll_period
from apps.tailors.tests.helpers import create_tailor

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


def test_initial_settlement_summary(client, staff, finalized_entry):
    response = client.get(entry_settlement_url(finalized_entry.id), **_auth(staff))
    assert response.status_code == 200
    settlement = response.json()["settlement"]
    assert settlement["gross_payable"] == 750.0
    assert settlement["advance_deductions"] == 0.0
    assert settlement["payments_recorded"] == 0.0
    assert settlement["outstanding_payable"] == 750.0
    assert settlement["settlement_status"] == "UNPAID"
    assert settlement["payment_count"] == 0


def test_gross_payable_matches_phase6(client, staff, finalized_entry):
    summary = settlement_summary(finalized_entry)
    assert (
        summary["gross_payable"] == finalized_entry.total_payable == Decimal("750.00")
    )


def test_apply_advance_reduces_outstanding(client, staff, finalized_entry):
    advance = create_advance(finalized_entry.tailor, amount="300.00")

    response = client.post(
        entry_apply_advance_url(finalized_entry.id),
        {"advance_id": advance.id},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    settlement = response.json()["settlement"]
    assert settlement["advance_deductions"] == 300.0
    assert settlement["outstanding_payable"] == 450.0
    assert settlement["settlement_status"] == "PARTIALLY_PAID"

    advance.refresh_from_db()
    assert advance.status == SalaryAdvance.Status.DEDUCTED
    assert advance.payroll_entry_id == finalized_entry.id
    assert advance.deducted_at is not None


def test_advance_cannot_be_deducted_twice(client, staff, finalized_entry):
    advance = create_advance(finalized_entry.tailor, amount="300.00")
    client.post(
        entry_apply_advance_url(finalized_entry.id),
        {"advance_id": advance.id},
        content_type="application/json",
        **_auth(staff),
    )

    response = client.post(
        entry_apply_advance_url(finalized_entry.id),
        {"advance_id": advance.id},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "already been deducted" in response.json()["error"]["message"].lower()


def test_advance_wrong_tailor_rejected(client, staff, finalized_entry):
    other = create_tailor("Other Tailor")
    advance = create_advance(other, amount="300.00")

    response = client.post(
        entry_apply_advance_url(finalized_entry.id),
        {"advance_id": advance.id},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "different tailor" in response.json()["error"]["message"].lower()


def test_advance_exceeding_outstanding_rejected(client, staff, finalized_entry):
    advance = create_advance(finalized_entry.tailor, amount="900.00")

    response = client.post(
        entry_apply_advance_url(finalized_entry.id),
        {"advance_id": advance.id},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "exceeds" in response.json()["error"]["message"].lower()

    advance.refresh_from_db()
    assert advance.status == SalaryAdvance.Status.OUTSTANDING


def test_advance_requires_finalized_period(client, staff):
    tailor = create_tailor()
    period = create_payroll_period(status=PayrollPeriod.Status.CALCULATED)
    entry = period.entries.create(tailor=tailor, total_payable=Decimal("750.00"))
    advance = create_advance(tailor, amount="300.00")

    response = client.post(
        entry_apply_advance_url(entry.id),
        {"advance_id": advance.id},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "finalized" in response.json()["error"]["message"].lower()


def test_owner_cannot_apply_advance(client, owner, finalized_entry):
    advance = create_advance(finalized_entry.tailor, amount="300.00")
    response = client.post(
        entry_apply_advance_url(finalized_entry.id),
        {"advance_id": advance.id},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_payment_reduces_outstanding(client, staff, finalized_entry):
    create_advance(finalized_entry.tailor, amount="300.00")
    response = client.post(
        entry_payments_url(finalized_entry.id),
        _payment_payload(amount="200.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    settlement = response.json()["settlement"]
    assert settlement["advance_deductions"] == 0.0
    assert settlement["payments_recorded"] == 200.0
    assert settlement["outstanding_payable"] == 550.0


def test_fully_settled_status(client, staff, finalized_entry):
    response = client.post(
        entry_payments_url(finalized_entry.id),
        _payment_payload(amount="750.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["settlement"]["settlement_status"] == "SETTLED"
    assert outstanding_payable(finalized_entry) == Decimal("0.00")


def test_settle_action_pays_full_outstanding(client, staff, finalized_entry):
    response = client.post(
        entry_settle_url(finalized_entry.id),
        _payment_payload(amount="999.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    settlement = response.json()["settlement"]
    assert settlement["payments_recorded"] == 750.0
    assert settlement["outstanding_payable"] == 0.0
    assert settlement["settlement_status"] == "SETTLED"


def test_settle_when_already_settled(client, staff, finalized_entry):
    client.post(
        entry_settle_url(finalized_entry.id),
        _payment_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    response = client.post(
        entry_settle_url(finalized_entry.id),
        _payment_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "already fully settled" in response.json()["error"]["message"].lower()


def test_owner_cannot_settle(client, owner, finalized_entry):
    response = client.post(
        entry_settle_url(finalized_entry.id),
        _payment_payload(),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_concurrent_payments_cannot_overpay():
    from threading import Thread

    from django.db import connections
    from rest_framework.exceptions import ValidationError

    entry = create_finalized_entry()
    staff = make_staff()
    assert entry.total_payable == Decimal("750.00")

    errors = []

    def record(amount):
        try:
            record_payment(
                entry=entry,
                amount=amount,
                payment_date=TODAY,
                payment_method=PayrollPayment.Method.CASH,
                recorded_by=staff,
            )
        except ValidationError as exc:
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [Thread(target=record, args=(Decimal("500.00"),)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(errors) == 1
    assert PayrollPayment.objects.filter(payroll_entry=entry).count() == 1
    assert PayrollPayment.objects.get(payroll_entry=entry).amount == Decimal("500.00")
    assert outstanding_payable(entry) == Decimal("250.00")


def test_period_list_exposes_period_settlement(client, staff, finalized_entry):
    period_id = finalized_entry.payroll_period_id
    response = client.get("/api/v1/payroll/periods/", **_auth(staff))
    assert response.status_code == 200
    period = next(p for p in response.json()["results"] if p["id"] == period_id)
    settlement = period["settlement"]
    assert settlement["gross_payable"] == 750.0
    assert settlement["advance_deductions"] == 0.0
    assert settlement["payments_recorded"] == 0.0
    assert settlement["outstanding_payable"] == 750.0
    assert settlement["settlement_status"] == "UNPAID"
    assert settlement["payment_count"] == 0


def test_period_settlement_aggregates_entries(client, staff, finalized_entry, owner):
    period = finalized_entry.payroll_period
    second_tailor = create_tailor()
    second_entry = PayrollEntry.objects.create(
        payroll_period=period,
        tailor=second_tailor,
        completed_pieces=2,
        piece_rate_earnings=Decimal("300.00"),
        attendance_amount=Decimal("0.00"),
        total_payable=Decimal("300.00"),
    )

    apply_advance(
        entry=finalized_entry,
        advance=create_advance(finalized_entry.tailor, "200.00"),
        recorded_by=staff,
    )
    create_payment(finalized_entry, "400.00")

    summary = period_settlement_summary(period)
    assert summary["gross_payable"] == Decimal("1050.00")
    assert summary["advance_deductions"] == Decimal("200.00")
    assert summary["payments_recorded"] == Decimal("400.00")
    assert summary["outstanding_payable"] == Decimal("450.00")
    assert summary["settlement_status"] == "PARTIALLY_PAID"
    assert summary["payment_count"] == 1

    create_payment(second_entry, "300.00")
    summary = period_settlement_summary(period)
    assert summary["outstanding_payable"] == Decimal("150.00")
    assert summary["payment_count"] == 2


def test_draft_period_without_entries_is_unpaid(client, staff):
    period = create_payroll_period()
    summary = period_settlement_summary(period)
    assert summary["gross_payable"] == Decimal("0.00")
    assert summary["settlement_status"] == "UNPAID"
