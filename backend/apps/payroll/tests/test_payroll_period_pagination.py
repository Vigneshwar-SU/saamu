"""Payroll period list pagination, ordering and accessibility tests.

The Payroll page paginates at 7 records per page (an explicit exception to the
application-wide 6-per-page list standard). These tests pin the pagination
boundaries (0 / <7 / exactly 7 / 8 / 14 / 15), the newest-first deterministic
ordering, metadata correctness (count / next / previous), the guarantee that
every period is reachable exactly once across pages, and that OWNER/STAFF RBAC
and the payroll lifecycle remain unchanged.
"""

from datetime import date, timedelta

import pytest

from apps.customers.tests.helpers import auth_header
from apps.payroll.models import PayrollPeriod
from apps.payroll.tests.helpers import (
    create_payroll_period,
    make_owner,
    make_staff,
    payroll_calculate_url,
    payroll_finalize_url,
    payroll_periods_url,
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


def _period_ids(body):
    return [row["id"] for row in body["results"]]


def _fetch_all(client, user):
    """Follow ``next`` across every page, returning (last_body, ids)."""
    ids = []
    page = 1
    while True:
        body = client.get(payroll_periods_url(), {"page": page}, **_auth(user)).json()
        assert body["count"] >= len(ids)  # count is stable and >= collected rows
        ids.extend(_period_ids(body))
        if body["next"] is None:
            return body, ids
        page += 1


def _create_many(total):
    return [create_payroll_period() for _ in range(total)]


# ---------------------------------------------------------------------------
# Pagination boundaries
# ---------------------------------------------------------------------------


def test_empty_list(client, staff):
    body = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert body["count"] == 0
    assert body["results"] == []
    assert body["next"] is None
    assert body["previous"] is None


@pytest.mark.parametrize("total", [1, 3, 6])
def test_fewer_than_seven_periods_all_on_page_one(client, staff, total):
    _create_many(total)
    body = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert body["count"] == total
    assert len(body["results"]) == total
    assert body["next"] is None
    assert body["previous"] is None


def test_exactly_seven_periods_on_one_page(client, staff):
    created = _create_many(7)
    body = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert body["count"] == 7
    assert len(body["results"]) == 7
    assert body["next"] is None
    assert body["previous"] is None
    assert sorted(_period_ids(body)) == sorted(p.id for p in created)


def test_eight_periods_split_7_and_1(client, staff):
    created = _create_many(8)
    first = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert first["count"] == 8
    assert len(first["results"]) == 7
    assert first["next"] is not None
    assert first["previous"] is None

    second = client.get(payroll_periods_url(), {"page": 2}, **_auth(staff)).json()
    assert len(second["results"]) == 1
    assert second["next"] is None
    assert second["previous"] is not None

    all_ids = _period_ids(first) + _period_ids(second)
    assert sorted(all_ids) == sorted(p.id for p in created)
    assert len(set(all_ids)) == 8


def test_fourteen_periods_split_7_and_7(client, staff):
    created = _create_many(14)
    first = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert first["count"] == 14
    assert len(first["results"]) == 7
    assert first["next"] is not None
    assert first["previous"] is None

    second = client.get(payroll_periods_url(), {"page": 2}, **_auth(staff)).json()
    assert len(second["results"]) == 7
    assert second["next"] is None
    assert second["previous"] is not None

    all_ids = _period_ids(first) + _period_ids(second)
    assert sorted(all_ids) == sorted(p.id for p in created)
    assert len(set(all_ids)) == 14


def test_fifteen_periods_split_7_7_1(client, staff):
    created = _create_many(15)
    first = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert first["count"] == 15
    assert len(first["results"]) == 7

    second = client.get(payroll_periods_url(), {"page": 2}, **_auth(staff)).json()
    assert len(second["results"]) == 7

    third = client.get(payroll_periods_url(), {"page": 3}, **_auth(staff)).json()
    assert len(third["results"]) == 1
    assert third["next"] is None
    assert third["previous"] is not None

    all_ids = _period_ids(first) + _period_ids(second) + _period_ids(third)
    assert sorted(all_ids) == sorted(p.id for p in created)
    assert len(set(all_ids)) == 15


def test_page_size_query_override_still_works(client, staff):
    _create_many(10)
    body = client.get(payroll_periods_url(), {"page_size": 3}, **_auth(staff)).json()
    assert body["count"] == 10
    assert len(body["results"]) == 3
    assert body["next"] is not None


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


def test_newest_periods_first(client, staff):
    old = create_payroll_period(
        period_start=TODAY - timedelta(days=90), period_end=TODAY - timedelta(days=60)
    )
    mid = create_payroll_period(
        period_start=TODAY - timedelta(days=30), period_end=TODAY - timedelta(days=15)
    )
    recent = create_payroll_period(period_start=TODAY, period_end=TODAY)
    body = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert _period_ids(body) == [recent.id, mid.id, old.id]


def test_ordering_stable_for_identical_dates(client, staff):
    created = _create_many(10)
    first = client.get(payroll_periods_url(), **_auth(staff)).json()
    second = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert _period_ids(first) == _period_ids(second)
    # Newest (last created) first across all pages; ``id DESC`` is the
    # deterministic tie-breaker.
    _, ids = _fetch_all(client, staff)
    assert ids == [p.id for p in reversed(created)]


def test_all_periods_reachable_exactly_once(client, staff):
    created = _create_many(15)
    last_body, ids = _fetch_all(client, staff)
    assert last_body["count"] == 15
    assert sorted(ids) == sorted(p.id for p in created)
    assert len(ids) == len(set(ids)) == 15


# ---------------------------------------------------------------------------
# RBAC and lifecycle remain unchanged
# ---------------------------------------------------------------------------


def test_owner_can_read_paginated_list(client, owner):
    _create_many(9)
    body = client.get(payroll_periods_url(), **_auth(owner)).json()
    assert body["count"] == 9
    assert len(body["results"]) == 7

    second = client.get(payroll_periods_url(), {"page": 2}, **_auth(owner)).json()
    assert len(second["results"]) == 2


def test_owner_mutations_still_forbidden(client, owner):
    _create_many(8)
    body = client.get(payroll_periods_url(), **_auth(owner)).json()
    assert body["count"] == 8

    response = client.post(
        payroll_periods_url(),
        {"period_start": str(TODAY), "period_end": str(TODAY)},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_staff_can_read_list(client, staff):
    _create_many(8)
    body = client.get(payroll_periods_url(), **_auth(staff)).json()
    assert body["count"] == 8
    assert len(body["results"]) == 7


def test_staff_create_calculate_finalize_unaffected(client, staff):
    response = client.post(
        payroll_periods_url(),
        {
            "period_start": str(TODAY - timedelta(days=6)),
            "period_end": str(TODAY),
            "notes": "Pagination regression check",
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    period_id = response.json()["id"]

    assert (
        client.post(
            payroll_calculate_url(period_id),
            content_type="application/json",
            **_auth(staff),
        ).status_code
        == 200
    )
    period = PayrollPeriod.objects.get(pk=period_id)
    assert period.status == PayrollPeriod.Status.CALCULATED

    assert (
        client.post(
            payroll_finalize_url(period_id),
            content_type="application/json",
            **_auth(staff),
        ).status_code
        == 200
    )
    period.refresh_from_db()
    assert period.status == PayrollPeriod.Status.FINALIZED
