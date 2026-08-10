"""Salary configuration list pagination, ordering and accessibility tests.

The Salary Configuration page uses the application's standard list pagination
(6 records per page) via the shared ``SaamuPageNumberPagination``. These tests
pin the pagination boundaries (0 / <6 / exactly 6 / 7 / 12 / 13), the
newest-first deterministic ordering (``-effective_from`` then ``-id``),
metadata correctness (``count`` / ``next`` / ``previous``), the guarantee that
every configuration is reachable exactly once across pages, and that
OWNER/STAFF RBAC and the CRUD lifecycle remain unchanged.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.customers.tests.helpers import auth_header
from apps.payroll.models import TailorSalaryConfiguration
from apps.payroll.tests.helpers import (
    make_owner,
    make_staff,
    salary_configuration_url,
    salary_configurations_url,
)
from apps.tailors.tests.helpers import create_tailor

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


def _create_config(tailor, **extra):
    defaults = {
        "salary_model": TailorSalaryConfiguration.SalaryModel.PER_GARMENT,
        "fixed_salary_amount": Decimal("0.00"),
        "effective_from": TODAY - timedelta(days=30),
        "is_active": True,
    }
    defaults.update(extra)
    return TailorSalaryConfiguration.objects.create(tailor=tailor, **defaults)


def _config_payload(tailor, **extra):
    payload = {
        "tailor": tailor.id,
        "salary_model": "FIXED_SALARY",
        "fixed_salary_amount": 5000,
        "effective_from": str(TODAY - timedelta(days=30)),
        "is_active": True,
        "notes": "",
    }
    payload.update(extra)
    return payload


def _config_ids(body):
    return [row["id"] for row in body["results"]]


def _create_many(total):
    return [_create_config(create_tailor()) for _ in range(total)]


def _fetch_all(client, user):
    """Follow ``next`` across every page, returning (last_body, ids)."""
    ids = []
    page = 1
    while True:
        body = client.get(
            salary_configurations_url(), {"page": page}, **_auth(user)
        ).json()
        assert body["count"] >= len(ids)  # count is stable and >= collected rows
        ids.extend(_config_ids(body))
        if body["next"] is None:
            return body, ids
        page += 1


# ---------------------------------------------------------------------------
# Pagination boundaries (6 per page)
# ---------------------------------------------------------------------------


def test_empty_list(client, staff):
    body = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert body["count"] == 0
    assert body["results"] == []
    assert body["next"] is None
    assert body["previous"] is None


@pytest.mark.parametrize("total", [1, 3, 5])
def test_fewer_than_six_configs_all_on_page_one(client, staff, total):
    created = _create_many(total)
    body = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert body["count"] == total
    assert len(body["results"]) == total
    assert body["next"] is None
    assert body["previous"] is None
    assert sorted(_config_ids(body)) == sorted(c.id for c in created)


def test_exactly_six_configs_on_one_page(client, staff):
    created = _create_many(6)
    body = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert body["count"] == 6
    assert len(body["results"]) == 6
    assert body["next"] is None
    assert body["previous"] is None
    assert sorted(_config_ids(body)) == sorted(c.id for c in created)


def test_seven_configs_split_6_and_1(client, staff):
    created = _create_many(7)
    first = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert first["count"] == 7
    assert len(first["results"]) == 6
    assert first["next"] is not None
    assert first["previous"] is None

    second = client.get(
        salary_configurations_url(), {"page": 2}, **_auth(staff)
    ).json()
    assert len(second["results"]) == 1
    assert second["next"] is None
    assert second["previous"] is not None

    all_ids = _config_ids(first) + _config_ids(second)
    assert sorted(all_ids) == sorted(c.id for c in created)
    assert len(set(all_ids)) == 7


def test_twelve_configs_split_6_and_6(client, staff):
    created = _create_many(12)
    first = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert first["count"] == 12
    assert len(first["results"]) == 6
    assert first["next"] is not None
    assert first["previous"] is None

    second = client.get(
        salary_configurations_url(), {"page": 2}, **_auth(staff)
    ).json()
    assert len(second["results"]) == 6
    assert second["next"] is None
    assert second["previous"] is not None

    all_ids = _config_ids(first) + _config_ids(second)
    assert sorted(all_ids) == sorted(c.id for c in created)
    assert len(set(all_ids)) == 12


def test_thirteen_configs_split_6_6_1(client, staff):
    created = _create_many(13)
    first = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert first["count"] == 13
    assert len(first["results"]) == 6

    second = client.get(
        salary_configurations_url(), {"page": 2}, **_auth(staff)
    ).json()
    assert len(second["results"]) == 6

    third = client.get(
        salary_configurations_url(), {"page": 3}, **_auth(staff)
    ).json()
    assert len(third["results"]) == 1
    assert third["next"] is None
    assert third["previous"] is not None

    all_ids = _config_ids(first) + _config_ids(second) + _config_ids(third)
    assert sorted(all_ids) == sorted(c.id for c in created)
    assert len(set(all_ids)) == 13


def test_page_size_query_override_still_works(client, staff):
    _create_many(10)
    body = client.get(
        salary_configurations_url(), {"page_size": 2}, **_auth(staff)
    ).json()
    assert body["count"] == 10
    assert len(body["results"]) == 2
    assert body["next"] is not None


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


def test_newest_effective_configs_first(client, staff):
    old = _create_config(
        create_tailor(),
        effective_from=TODAY - timedelta(days=90),
    )
    mid = _create_config(
        create_tailor(),
        effective_from=TODAY - timedelta(days=30),
    )
    recent = _create_config(create_tailor(), effective_from=TODAY)
    body = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert _config_ids(body) == [recent.id, mid.id, old.id]


def test_ordering_stable_for_identical_dates(client, staff):
    created = _create_many(10)
    first = client.get(salary_configurations_url(), **_auth(staff)).json()
    second = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert _config_ids(first) == _config_ids(second)
    # Newest (last created) first; ``id DESC`` is the deterministic tie-breaker.
    _, ids = _fetch_all(client, staff)
    assert ids == [c.id for c in reversed(created)]


def test_all_configs_reachable_exactly_once(client, staff):
    created = _create_many(13)
    last_body, ids = _fetch_all(client, staff)
    assert last_body["count"] == 13
    assert sorted(ids) == sorted(c.id for c in created)
    assert len(ids) == len(set(ids)) == 13


# ---------------------------------------------------------------------------
# RBAC and CRUD remain unchanged
# ---------------------------------------------------------------------------


def test_owner_can_read_paginated_list(client, owner):
    _create_many(9)
    body = client.get(salary_configurations_url(), **_auth(owner)).json()
    assert body["count"] == 9
    assert len(body["results"]) == 6

    second = client.get(
        salary_configurations_url(), {"page": 2}, **_auth(owner)
    ).json()
    assert len(second["results"]) == 3


def test_owner_mutations_still_forbidden(client, owner):
    config = _create_config(create_tailor())
    body = client.get(salary_configurations_url(), **_auth(owner)).json()
    assert body["count"] == 1

    response = client.post(
        salary_configurations_url(),
        _config_payload(create_tailor()),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403

    response = client.patch(
        salary_configuration_url(config.id),
        {"is_active": False},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_staff_can_read_list(client, staff):
    _create_many(8)
    body = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert body["count"] == 8
    assert len(body["results"]) == 6


def test_staff_crud_unaffected(client, staff):
    tailor = create_tailor()
    response = client.post(
        salary_configurations_url(),
        _config_payload(tailor),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    config_id = response.json()["id"]

    # Patch (edit) still works and the record stays listable.
    response = client.patch(
        salary_configuration_url(config_id),
        {"fixed_salary_amount": 7500},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["fixed_salary_amount"] == 7500.0

    # The updated record is still reachable on page 1 of a paginated list.
    body = client.get(salary_configurations_url(), **_auth(staff)).json()
    assert body["count"] == 1
    assert body["results"][0]["id"] == config_id
