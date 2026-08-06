"""Payroll period lifecycle, calculation and RBAC tests."""

from datetime import date, timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.attendance.models import Attendance
from apps.attendance.tests.helpers import create_attendance
from apps.customers.tests.helpers import auth_header
from apps.payments.services import period_settlement_summary, settlement_summary
from apps.payroll.models import PayrollEntry, PayrollPeriod
from apps.payroll.tests.helpers import (
    create_completed_assignment,
    create_payroll_period,
    make_owner,
    make_staff,
    payroll_calculate_url,
    payroll_entries_url,
    payroll_finalize_url,
    payroll_period_url,
    payroll_periods_url,
    payroll_tailor_detail_url,
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


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _setup_work(customer, garment_quantities, tailor, rate="150.00"):
    order = create_order_with_items(customer, garment_quantities)
    create_piece_rate(garment_type=list(garment_quantities)[0], rate_per_piece=rate)
    return order


def test_anonymous_denied(client):
    assert client.get(payroll_periods_url()).status_code == 401
    assert (
        client.post(
            payroll_periods_url(),
            {"period_start": str(TODAY), "period_end": str(TODAY)},
            content_type="application/json",
        ).status_code
        == 401
    )
    assert client.get(payroll_entries_url()).status_code == 401


def test_owner_can_read_periods(client, owner):
    period = create_payroll_period()
    response = client.get(payroll_periods_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = client.get(payroll_period_url(period.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["status"] == "DRAFT"


def test_owner_mutation_forbidden(client, owner):
    response = client.post(
        payroll_periods_url(),
        {"period_start": str(TODAY), "period_end": str(TODAY)},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403

    period = create_payroll_period()
    assert (
        client.post(
            payroll_calculate_url(period.id),
            content_type="application/json",
            **_auth(owner),
        ).status_code
        == 403
    )
    calculated = create_payroll_period(status=PayrollPeriod.Status.CALCULATED)
    assert (
        client.post(
            payroll_finalize_url(calculated.id),
            content_type="application/json",
            **_auth(owner),
        ).status_code
        == 403
    )


def test_staff_creates_period(client, staff):
    response = client.post(
        payroll_periods_url(),
        {
            "period_start": str(TODAY - timedelta(days=6)),
            "period_end": str(TODAY),
            "notes": "First fortnight",
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "DRAFT"
    assert data["period_start"] == str(TODAY - timedelta(days=6))
    assert data["created_by_name"] == staff.username


def test_invalid_date_range_rejected(client, staff):
    response = client.post(
        payroll_periods_url(),
        {"period_start": str(TODAY), "period_end": str(TODAY - timedelta(days=1))},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "period_end" in response.json()["error"]["details"]


def test_periods_list_shows_aggregates(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 6}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 4, 4, "150.00", timezone.now())
    create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
    period.calculate()

    response = client.get(payroll_periods_url(), **_auth(staff))
    data = response.json()["results"][0]
    assert data["total_completed_pieces"] == 6
    assert data["total_piece_rate_earnings"] == 900.0
    assert data["total_payable"] == 900.0
    assert data["entry_count"] == 1


def test_calculation_includes_completed_and_excludes_outstanding(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 8}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )

    create_completed_assignment(tailor, item, 4, 4, "150.00", timezone.now())
    create_completed_assignment(tailor, item, 4, 4, "150.00", timezone.now())
    # In-progress assignment inside the period: must not count.
    from apps.tailors.models import WorkAssignment

    WorkAssignment.objects.create(
        tailor=tailor,
        order_item=item,
        assigned_quantity=3,
        completed_quantity=1,
        status=WorkAssignment.Status.IN_PROGRESS,
        rate_per_piece_snapshot="150.00",
    )

    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period"]["status"] == "CALCULATED"
    assert data["period"]["total_completed_pieces"] == 8
    assert data["period"]["total_piece_rate_earnings"] == 1200.0
    assert data["period"]["total_payable"] == 1200.0
    assert len(data["entries"]) == 1
    assert data["entries"][0]["completed_pieces"] == 8


def test_inclusive_period_boundaries(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 9}, tailor)
    item = get_order_item(order, "SHIRT")

    period_start = TODAY - timedelta(days=10)
    period_end = TODAY - timedelta(days=5)
    period = create_payroll_period(period_start=period_start, period_end=period_end)

    # Exactly on the start boundary and on the end boundary.
    create_completed_assignment(
        tailor, item, 3, 3, "100.00", timezone.now() - timedelta(days=10)
    )
    create_completed_assignment(
        tailor, item, 3, 3, "100.00", timezone.now() - timedelta(days=5)
    )
    # Outside the period (before start / after end): must be excluded.
    create_completed_assignment(
        tailor, item, 2, 2, "100.00", timezone.now() - timedelta(days=11)
    )
    create_completed_assignment(
        tailor, item, 1, 1, "100.00", timezone.now() - timedelta(days=4)
    )

    period.calculate()

    entry = period.entries.get(tailor=tailor)
    assert entry.completed_pieces == 6
    assert entry.piece_rate_earnings == 600.0


def test_historical_rate_snapshot_invariance(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 5}, tailor, rate="125.00")
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )

    create_completed_assignment(tailor, item, 3, 3, "125.00", timezone.now())

    # Current piece rate later changed to 150; payroll must stay at snapshot.
    from apps.tailors.models import PieceRate

    PieceRate.objects.filter(garment_type="SHIRT").update(rate_per_piece="150.00")
    period.calculate()

    entry = period.entries.get(tailor=tailor)
    assert entry.completed_pieces == 3
    assert entry.piece_rate_earnings == 375.0


def test_multiple_tailors_aggregation(client, staff):
    customer = create_customer()
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    order = _setup_work(customer, {"SHIRT": 10}, tailor_a)
    item = get_order_item(order, "SHIRT")
    # Current rate for SHIRT changed to 200; snapshots on each assignment stay as set.
    from apps.tailors.models import PieceRate

    PieceRate.objects.filter(garment_type="SHIRT").update(rate_per_piece="200.00")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )

    create_completed_assignment(tailor_a, item, 3, 3, "150.00", timezone.now())
    create_completed_assignment(tailor_b, item, 4, 4, "200.00", timezone.now())

    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period"]["total_completed_pieces"] == 7
    assert data["period"]["total_piece_rate_earnings"] == 1250.0
    assert len(data["entries"]) == 2

    by_name = {e["tailor"]["name"]: e for e in data["entries"]}
    assert by_name["Tailor A"]["completed_pieces"] == 3
    assert by_name["Tailor A"]["piece_rate_earnings"] == 450.0
    assert by_name["Tailor B"]["completed_pieces"] == 4
    assert by_name["Tailor B"]["piece_rate_earnings"] == 800.0


def test_attendance_aggregation(client, staff):
    tailor = create_tailor()
    create_attendance(tailor, status=Attendance.Status.PRESENT)
    create_attendance(
        tailor,
        attendance_date=TODAY - timedelta(days=1),
        status=Attendance.Status.HALF_DAY,
    )
    create_attendance(
        tailor,
        attendance_date=TODAY - timedelta(days=2),
        status=Attendance.Status.ABSENT,
    )
    create_attendance(
        tailor,
        attendance_date=TODAY - timedelta(days=3),
        status=Attendance.Status.PRESENT,
    )
    # Outside the period.
    create_attendance(
        tailor,
        attendance_date=TODAY - timedelta(days=30),
        status=Attendance.Status.PRESENT,
    )

    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    entry = response.json()["entries"][0]
    assert entry["present_days"] == 2
    assert entry["half_days"] == 1
    assert entry["absent_days"] == 1
    assert entry["attendance_amount"] == 0.0
    assert entry["total_payable"] == 0.0


def test_recalculate_while_editable(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 10}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )

    create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
    period.calculate()
    first = period.entries.get(tailor=tailor)
    assert first.completed_pieces == 2

    create_completed_assignment(tailor, item, 3, 3, "150.00", timezone.now())
    period.calculate()

    period.refresh_from_db()
    assert period.status == PayrollPeriod.Status.CALCULATED
    entry = period.entries.get(tailor=tailor)
    assert entry.completed_pieces == 5
    assert entry.piece_rate_earnings == 750.0
    assert PayrollEntry.objects.filter(payroll_period=period).count() == 1


def test_finalized_recalculation_blocked(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 5}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
    period.calculate()
    period.status = PayrollPeriod.Status.FINALIZED
    period.save(update_fields=["status", "updated_at"])

    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "finalized" in response.json()["error"]["message"].lower()


def test_finalize_requires_calculated(client, staff):
    period = create_payroll_period(status=PayrollPeriod.Status.DRAFT)
    response = client.post(
        payroll_finalize_url(period.id), content_type="application/json", **_auth(staff)
    )
    assert response.status_code == 400
    assert "calculate" in response.json()["error"]["message"].lower()


def test_finalize_works_and_blocks_again(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 5}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
    period.calculate()

    response = client.post(
        payroll_finalize_url(period.id), content_type="application/json", **_auth(staff)
    )
    assert response.status_code == 200
    assert response.json()["period"]["status"] == "FINALIZED"

    response = client.post(
        payroll_finalize_url(period.id), content_type="application/json", **_auth(staff)
    )
    assert response.status_code == 400

    period.refresh_from_db()
    assert period.status == PayrollPeriod.Status.FINALIZED


def test_entries_list_filters(client, staff):
    customer = create_customer()
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    order = _setup_work(customer, {"SHIRT": 8}, tailor_a)
    item = get_order_item(order, "SHIRT")
    period_a = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    period_b = create_payroll_period(
        period_start=TODAY - timedelta(days=14), period_end=TODAY - timedelta(days=8)
    )
    create_completed_assignment(tailor_a, item, 2, 2, "150.00", timezone.now())
    create_completed_assignment(tailor_b, item, 2, 2, "150.00", timezone.now())
    period_a.calculate()
    period_b.calculate()

    response = client.get(
        payroll_entries_url(), {"period": period_a.id}, **_auth(staff)
    )
    assert response.status_code == 200
    assert response.json()["count"] == 2

    response = client.get(
        payroll_entries_url(),
        {"period": period_a.id, "tailor": tailor_a.id},
        **_auth(staff),
    )
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["tailor"]["id"] == tailor_a.id


def test_tailor_detail_breakdown(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 10, "PANT": 4}, tailor)
    shirt = get_order_item(order, "SHIRT")
    pant = get_order_item(order, "PANT")
    create_piece_rate(garment_type="PANT", rate_per_piece="200.00")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )

    create_completed_assignment(tailor, shirt, 3, 3, "150.00", timezone.now())
    create_completed_assignment(tailor, pant, 2, 2, "200.00", timezone.now())
    period.calculate()

    response = client.get(
        payroll_tailor_detail_url(period.id, tailor.id), **_auth(staff)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tailor"]["name"] == tailor.full_name
    assert data["entry"]["completed_pieces"] == 5
    assert data["entry"]["piece_rate_earnings"] == 850.0
    assert len(data["assignments"]) == 2

    assignments = {a["garment_code"]: a for a in data["assignments"]}
    assert assignments["SHIRT"]["completed_quantity"] == 3
    assert assignments["SHIRT"]["earned_amount"] == 450.0
    assert assignments["PANT"]["earned_amount"] == 400.0


def test_owner_can_read_entries_and_tailor_detail(client, owner):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 4}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
    period.calculate()

    assert client.get(payroll_entries_url(), **_auth(owner)).status_code == 200
    response = client.get(
        payroll_tailor_detail_url(period.id, tailor.id), **_auth(owner)
    )
    assert response.status_code == 200
    assert len(response.json()["assignments"]) == 1


def test_archived_tailor_payroll_history_visible(client, staff):
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 4}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
    period.calculate()

    client.post(f"/api/v1/tailors/{tailor.id}/archive/", **_auth(staff))

    response = client.get(
        payroll_tailor_detail_url(period.id, tailor.id), **_auth(staff)
    )
    assert response.status_code == 200
    assert response.json()["tailor"]["is_active"] is False
    assert response.json()["entry"]["completed_pieces"] == 2


def test_period_list_aggregate_queries_are_bounded(client, staff):
    """Phase 15 N+1 regression: period list queries do not scale with rows.

    The period aggregates and settlement values are precomputed with queryset
    annotations, so listing any number of periods stays within a small constant
    number of queries instead of the previous per-period aggregate queries.
    """
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 12}, tailor)
    item = get_order_item(order, "SHIRT")
    for _ in range(3):
        period = create_payroll_period(
            period_start=TODAY - timedelta(days=7), period_end=TODAY
        )
        create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
        period.calculate()

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(payroll_periods_url(), **_auth(staff))
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert data["results"][0]["total_payable"] == 900.0
    assert data["results"][0]["settlement"]["gross_payable"] == 900.0
    assert len(ctx) <= 10


def test_entry_list_settlement_queries_are_bounded(client, staff):
    """Phase 15 N+1 regression: entry list settlement does not query per row."""
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 8}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 4, 4, "150.00", timezone.now())
    period.calculate()

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(payroll_entries_url(), **_auth(staff))
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["settlement"]["gross_payable"] == 600.0
    assert len(ctx) <= 10


def test_precomputed_settlement_summary_matches_live(client, staff):
    """Precomputed settlement values must equal the live per-row computation."""
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 4}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
    period.calculate()

    entry = period.entries.get()
    live = settlement_summary(entry)
    precomputed = settlement_summary(
        entry,
        precomputed={
            "advance_deductions": live["advance_deductions"],
            "payments_recorded": live["payments_recorded"],
            "payment_count": live["payment_count"],
        },
    )
    assert precomputed == live


def test_precomputed_period_settlement_summary_matches_live(client, staff):
    """Precomputed period settlement values must equal the live computation."""
    customer = create_customer()
    tailor = create_tailor()
    order = _setup_work(customer, {"SHIRT": 4}, tailor)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())
    period.calculate()

    live = period_settlement_summary(period)
    precomputed = period_settlement_summary(
        period,
        precomputed={
            "gross_payable": live["gross_payable"],
            "advance_deductions": live["advance_deductions"],
            "payments_recorded": live["payments_recorded"],
            "payment_count": live["payment_count"],
        },
    )
    assert precomputed == live
