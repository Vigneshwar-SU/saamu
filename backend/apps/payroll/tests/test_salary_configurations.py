"""Tailor salary configuration tests: models, RBAC, calculation and snapshots.

Covers the three salary models (PER_GARMENT / FIXED_SALARY / MIXED), the
effective-date rules, configuration snapshots onto payroll entries, finalized
immutability and the settlement regression across the salary models.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.customers.tests.helpers import auth_header
from apps.payments.tests.helpers import (
    create_advance,
    entry_apply_advance_url,
    entry_payments_url,
    entry_settle_url,
    entry_settlement_url,
)
from apps.payroll.models import PayrollPeriod, TailorSalaryConfiguration
from apps.payroll.tests.helpers import (
    create_completed_assignment,
    create_payroll_period,
    make_owner,
    make_staff,
    payroll_calculate_url,
    payroll_salary_breakdown_url,
    salary_configuration_url,
    salary_configurations_url,
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


def _config_payload(tailor, **extra):
    payload = {
        "tailor": tailor.id,
        "salary_model": "PER_GARMENT",
        "fixed_salary_amount": 0,
        "effective_from": str(TODAY - timedelta(days=30)),
        "is_active": True,
        "notes": "",
    }
    payload.update(extra)
    return payload


def _create_config(tailor, salary_model, fixed_salary_amount, **extra):
    defaults = {
        "salary_model": salary_model,
        "fixed_salary_amount": Decimal(fixed_salary_amount),
        "effective_from": TODAY - timedelta(days=30),
        "is_active": True,
    }
    defaults.update(extra)
    return TailorSalaryConfiguration.objects.create(tailor=tailor, **defaults)


def _setup_period_with_work(tailor, quantity=5, rate="150.00"):
    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 10})
    create_piece_rate(garment_type="SHIRT", rate_per_piece=rate)
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    create_completed_assignment(tailor, item, quantity, quantity, rate, timezone.now())
    return period


def _payment_payload(amount="300.00"):
    return {
        "amount": amount,
        "payment_date": str(TODAY),
        "payment_method": "CASH",
        "reference": "",
        "notes": "",
    }


def test_anonymous_denied(client):
    assert client.get(salary_configurations_url()).status_code == 401
    response = client.post(
        salary_configurations_url(),
        _config_payload(create_tailor()),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_staff_creates_all_salary_models(client, staff):
    per_garment_tailor = create_tailor()
    response = client.post(
        salary_configurations_url(),
        _config_payload(per_garment_tailor),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["salary_model"] == "PER_GARMENT"
    assert data["salary_model_display"] == "Per Garment"
    assert data["fixed_salary_amount"] == 0.0
    assert data["created_by_name"] == staff.username
    assert data["tailor"]["id"] == per_garment_tailor.id

    fixed = client.post(
        salary_configurations_url(),
        _config_payload(
            create_tailor("Fixed Tailor"),
            salary_model="FIXED_SALARY",
            fixed_salary_amount=5000,
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert fixed.status_code == 201
    assert fixed.json()["salary_model"] == "FIXED_SALARY"
    assert fixed.json()["fixed_salary_amount"] == 5000.0

    mixed = client.post(
        salary_configurations_url(),
        _config_payload(
            create_tailor("Mixed Tailor"),
            salary_model="MIXED",
            fixed_salary_amount=3000,
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert mixed.status_code == 201
    assert mixed.json()["salary_model"] == "MIXED"
    assert mixed.json()["fixed_salary_amount"] == 3000.0


def test_fixed_and_mixed_require_positive_fixed_salary(client, staff):
    tailor = create_tailor()
    for model in ("FIXED_SALARY", "MIXED"):
        response = client.post(
            salary_configurations_url(),
            _config_payload(tailor, salary_model=model, fixed_salary_amount=0),
            content_type="application/json",
            **_auth(staff),
        )
        assert response.status_code == 400
        assert "fixed_salary_amount" in response.json()["error"]["details"]

    missing = client.post(
        salary_configurations_url(),
        {
            "tailor": tailor.id,
            "salary_model": "FIXED_SALARY",
            "effective_from": str(TODAY - timedelta(days=30)),
        },
        content_type="application/json",
        **_auth(staff),
    )
    assert missing.status_code == 400
    assert "fixed_salary_amount" in missing.json()["error"]["details"]


def test_negative_fixed_salary_rejected(client, staff):
    tailor = create_tailor()
    response = client.post(
        salary_configurations_url(),
        _config_payload(tailor, salary_model="FIXED_SALARY", fixed_salary_amount=-100),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_effective_date_validation(client, staff):
    tailor = create_tailor()
    response = client.post(
        salary_configurations_url(),
        _config_payload(
            tailor,
            effective_from=str(TODAY),
            effective_to=str(TODAY - timedelta(days=1)),
        ),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "effective_to" in response.json()["error"]["details"]


def test_owner_read_only(client, owner):
    tailor = create_tailor()
    config = _create_config(tailor, "FIXED_SALARY", "5000.00")

    response = client.get(salary_configurations_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = client.get(salary_configuration_url(config.id), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["salary_model"] == "FIXED_SALARY"
    assert response.json()["tailor"]["name"] == tailor.full_name

    response = client.post(
        salary_configurations_url(),
        _config_payload(tailor),
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


def test_created_by_always_authenticated_user(client, staff):
    tailor = create_tailor()
    response = client.post(
        salary_configurations_url(),
        _config_payload(tailor, created_by=999),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["created_by_name"] == staff.username


def test_list_filters(client, staff):
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    _create_config(tailor_a, "FIXED_SALARY", "5000.00")
    _create_config(
        tailor_b,
        "MIXED",
        "2000.00",
        effective_from=TODAY - timedelta(days=20),
        is_active=False,
    )

    response = client.get(
        salary_configurations_url(), {"tailor": tailor_a.id}, **_auth(staff)
    )
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["tailor"]["id"] == tailor_a.id

    response = client.get(
        salary_configurations_url(), {"salary_model": "MIXED"}, **_auth(staff)
    )
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["salary_model"] == "MIXED"

    response = client.get(
        salary_configurations_url(), {"is_active": "false"}, **_auth(staff)
    )
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["is_active"] is False


def test_staff_patches_config(client, staff):
    tailor = create_tailor()
    config = _create_config(tailor, "PER_GARMENT", "0.00")

    response = client.patch(
        salary_configuration_url(config.id),
        {"salary_model": "FIXED_SALARY", "fixed_salary_amount": 4000},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["salary_model"] == "FIXED_SALARY"
    assert response.json()["fixed_salary_amount"] == 4000.0


def test_default_per_garment_calculation(client, staff):
    tailor = create_tailor()
    period = _setup_period_with_work(tailor)
    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    entry = response.json()["entries"][0]
    assert entry["salary_model"] == "PER_GARMENT"
    assert entry["salary_model_display"] == "Per Garment"
    assert entry["fixed_salary_amount"] == 0.0
    assert entry["completed_pieces"] == 5
    assert entry["piece_rate_earnings"] == 750.0
    assert entry["gross_salary"] == 750.0
    assert entry["total_payable"] == 750.0


def test_fixed_salary_calculation(client, staff):
    tailor = create_tailor()
    _create_config(tailor, "FIXED_SALARY", "5000.00")
    period = _setup_period_with_work(tailor)
    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    entry = response.json()["entries"][0]
    assert entry["salary_model"] == "FIXED_SALARY"
    assert entry["fixed_salary_amount"] == 5000.0
    assert entry["completed_pieces"] == 5
    assert entry["piece_rate_earnings"] == 0.0
    assert entry["gross_salary"] == 5000.0
    assert entry["total_payable"] == 5000.0

    period_data = response.json()["period"]
    assert period_data["total_fixed_salary"] == 5000.0
    assert period_data["total_gross_salary"] == 5000.0
    assert period_data["total_payable"] == 5000.0


def test_mixed_calculation(client, staff):
    tailor = create_tailor()
    _create_config(tailor, "MIXED", "3000.00")
    period = _setup_period_with_work(tailor)
    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    entry = response.json()["entries"][0]
    assert entry["salary_model"] == "MIXED"
    assert entry["salary_model_display"] == "Fixed + Per Garment"
    assert entry["fixed_salary_amount"] == 3000.0
    assert entry["piece_rate_earnings"] == 750.0
    assert entry["gross_salary"] == 3750.0
    assert entry["total_payable"] == 3750.0


def test_multiple_tailors_different_models(client, staff):
    fixed_tailor = create_tailor("Fixed Tailor")
    mixed_tailor = create_tailor("Mixed Tailor")
    piece_tailor = create_tailor("Piece Tailor")
    _create_config(fixed_tailor, "FIXED_SALARY", "4000.00")
    _create_config(mixed_tailor, "MIXED", "2000.00")

    customer = create_customer()
    order = create_order_with_items(customer, {"SHIRT": 20})
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")
    item = get_order_item(order, "SHIRT")
    period = create_payroll_period(
        period_start=TODAY - timedelta(days=7), period_end=TODAY
    )
    for tailor in (fixed_tailor, mixed_tailor, piece_tailor):
        create_completed_assignment(tailor, item, 2, 2, "150.00", timezone.now())

    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    entries = {e["tailor"]["name"]: e for e in response.json()["entries"]}

    assert entries["Fixed Tailor"]["salary_model"] == "FIXED_SALARY"
    assert entries["Fixed Tailor"]["fixed_salary_amount"] == 4000.0
    assert entries["Fixed Tailor"]["piece_rate_earnings"] == 0.0
    assert entries["Fixed Tailor"]["gross_salary"] == 4000.0

    assert entries["Mixed Tailor"]["salary_model"] == "MIXED"
    assert entries["Mixed Tailor"]["fixed_salary_amount"] == 2000.0
    assert entries["Mixed Tailor"]["piece_rate_earnings"] == 300.0
    assert entries["Mixed Tailor"]["gross_salary"] == 2300.0

    assert entries["Piece Tailor"]["salary_model"] == "PER_GARMENT"
    assert entries["Piece Tailor"]["fixed_salary_amount"] == 0.0
    assert entries["Piece Tailor"]["piece_rate_earnings"] == 300.0
    assert entries["Piece Tailor"]["gross_salary"] == 300.0

    period_data = response.json()["period"]
    assert period_data["total_fixed_salary"] == 6000.0
    assert period_data["total_gross_salary"] == 6600.0


def test_config_snapshot_and_recalculate(client, staff):
    tailor = create_tailor()
    _create_config(tailor, "FIXED_SALARY", "5000.00")
    period = _setup_period_with_work(tailor)
    period.calculate()
    entry = period.entries.get(tailor=tailor)
    assert entry.fixed_salary_amount == Decimal("5000.00")
    assert entry.total_payable == Decimal("5000.00")

    # A newer effective configuration supersedes the old one on recalculation.
    _create_config(tailor, "FIXED_SALARY", "6000.00")
    period.calculate()
    entry = period.entries.get(tailor=tailor)
    assert entry.fixed_salary_amount == Decimal("6000.00")
    assert entry.total_payable == Decimal("6000.00")
    assert PayrollPeriod.objects.get(pk=period.pk).entries.count() == 1


def test_config_changes_do_not_rewrite_finalized_payroll(client, staff):
    tailor = create_tailor()
    _create_config(tailor, "FIXED_SALARY", "5000.00")
    period = _setup_period_with_work(tailor)
    period.calculate()
    period.status = PayrollPeriod.Status.FINALIZED
    period.save(update_fields=["status", "updated_at"])

    TailorSalaryConfiguration.objects.filter(tailor=tailor).update(
        fixed_salary_amount=Decimal("9000.00")
    )

    response = client.post(
        payroll_calculate_url(period.id),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "finalized" in response.json()["error"]["message"].lower()

    entry = period.entries.get(tailor=tailor)
    assert entry.fixed_salary_amount == Decimal("5000.00")
    assert entry.total_payable == Decimal("5000.00")


def test_effective_from_on_period_start_applies(client, staff):
    tailor = create_tailor()
    _create_config(
        tailor,
        "FIXED_SALARY",
        "5000.00",
        effective_from=TODAY - timedelta(days=7),
    )
    period = _setup_period_with_work(tailor)
    period.calculate()
    entry = period.entries.get(tailor=tailor)
    assert entry.salary_model == "FIXED_SALARY"
    assert entry.fixed_salary_amount == Decimal("5000.00")


def test_config_starting_after_period_start_ignored(client, staff):
    tailor = create_tailor()
    _create_config(
        tailor,
        "FIXED_SALARY",
        "5000.00",
        effective_from=TODAY - timedelta(days=6),
    )
    period = _setup_period_with_work(tailor)
    period.calculate()
    entry = period.entries.get(tailor=tailor)
    assert entry.salary_model == "PER_GARMENT"
    assert entry.fixed_salary_amount == Decimal("0.00")
    assert entry.piece_rate_earnings == Decimal("750.00")


def test_ended_config_ignored(client, staff):
    tailor = create_tailor()
    _create_config(
        tailor,
        "FIXED_SALARY",
        "5000.00",
        effective_to=TODAY - timedelta(days=8),
    )
    period = _setup_period_with_work(tailor)
    period.calculate()
    entry = period.entries.get(tailor=tailor)
    assert entry.salary_model == "PER_GARMENT"
    assert entry.fixed_salary_amount == Decimal("0.00")


def test_inactive_config_ignored(client, staff):
    tailor = create_tailor()
    _create_config(tailor, "FIXED_SALARY", "5000.00", is_active=False)
    period = _setup_period_with_work(tailor)
    period.calculate()
    entry = period.entries.get(tailor=tailor)
    assert entry.salary_model == "PER_GARMENT"
    assert entry.fixed_salary_amount == Decimal("0.00")


def test_salary_breakdown_endpoint(client, staff):
    tailor = create_tailor()
    _create_config(tailor, "MIXED", "3000.00")
    period = _setup_period_with_work(tailor)
    period.calculate()

    response = client.get(
        payroll_salary_breakdown_url(period.id, tailor.id), **_auth(staff)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tailor"]["id"] == tailor.id
    breakdown = data["salary_breakdown"]
    assert breakdown["salary_model"] == "MIXED"
    assert breakdown["salary_model_display"] == "Fixed + Per Garment"
    assert breakdown["fixed_salary_amount"] == 3000.0
    assert breakdown["completed_pieces"] == 5
    assert breakdown["piece_rate_earnings"] == 750.0
    assert breakdown["gross_salary"] == 3750.0
    assert breakdown["attendance"] == {
        "present_days": 0,
        "half_days": 0,
        "absent_days": 0,
    }
    assert data["settlement"]["gross_payable"] == 3750.0
    assert data["settlement"]["settlement_status"] == "UNPAID"


def test_settlement_regression_with_fixed_salary(client, staff):
    tailor = create_tailor()
    _create_config(tailor, "FIXED_SALARY", "5000.00")
    period = _setup_period_with_work(tailor)
    period.calculate()
    period.status = PayrollPeriod.Status.FINALIZED
    period.save(update_fields=["status", "updated_at"])
    entry = period.entries.get(tailor=tailor)
    assert entry.total_payable == Decimal("5000.00")

    response = client.get(entry_settlement_url(entry.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["settlement"]["gross_payable"] == 5000.0

    advance = create_advance(tailor, amount="800.00")
    response = client.post(
        entry_apply_advance_url(entry.id),
        {"advance_id": advance.id},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["settlement"]["outstanding_payable"] == 4200.0
    assert response.json()["settlement"]["settlement_status"] == "PARTIALLY_PAID"

    response = client.post(
        entry_payments_url(entry.id),
        _payment_payload(amount="200.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["settlement"]["outstanding_payable"] == 4000.0

    response = client.post(
        entry_settle_url(entry.id),
        _payment_payload(amount="9999.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    settlement = response.json()["settlement"]
    assert settlement["outstanding_payable"] == 0.0
    assert settlement["settlement_status"] == "SETTLED"


def test_overpayment_impossible_for_fixed_salary(client, staff):
    tailor = create_tailor()
    _create_config(tailor, "FIXED_SALARY", "5000.00")
    period = _setup_period_with_work(tailor)
    period.calculate()
    period.status = PayrollPeriod.Status.FINALIZED
    period.save(update_fields=["status", "updated_at"])
    entry = period.entries.get(tailor=tailor)

    response = client.post(
        entry_payments_url(entry.id),
        _payment_payload(amount="6000.00"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    entry.refresh_from_db()
    assert entry.total_payable == Decimal("5000.00")
