"""Measurement history tests: immutable records, versions, current marker."""

import pytest

from apps.customers.models import Measurement
from apps.customers.tests.helpers import (
    create_customer,
    make_staff,
    measurement_detail_url,
    measurements_url,
    valid_pant_payload,
    valid_shirt_payload,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def customer():
    return create_customer()


def _auth(staff):
    from apps.authentication.tests.helpers import auth_header

    return {"HTTP_AUTHORIZATION": auth_header(staff)["HTTP_AUTHORIZATION"]}


def _get_history_versions(response):
    return [(item["version"], item["is_current"]) for item in response.json()]


def test_first_measurement_is_version_1_and_current(client, staff, customer):
    response = client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["version"] == 1
    assert response.json()["is_current"] is True


def test_new_shirt_version_preserves_history(client, staff, customer):
    client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    payload = valid_shirt_payload()
    payload["chest_circumference"] = 42.0
    second = client.post(
        measurements_url(customer.id),
        payload,
        content_type="application/json",
        **_auth(staff),
    )

    assert second.status_code == 201
    assert second.json()["version"] == 2
    assert second.json()["is_current"] is True
    assert Measurement.objects.count() == 2

    history = client.get(measurements_url(customer.id), **_auth(staff))
    versions = _get_history_versions(history)
    assert versions == [(1, False), (2, True)]


def test_only_one_current_version_per_garment(client, staff, customer):
    for index in range(3):
        payload = valid_shirt_payload()
        payload["chest_circumference"] = 38.0 + index
        client.post(
            measurements_url(customer.id),
            payload,
            content_type="application/json",
            **_auth(staff),
        )

    current = client.get(
        f"{measurements_url(customer.id)}?current=true", **_auth(staff)
    )
    assert len(current.json()) == 1
    assert current.json()[0]["version"] == 3
    assert current.json()[0]["is_current"] is True


def test_pant_history_is_independent_of_shirt(client, staff, customer):
    client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    client.post(
        measurements_url(customer.id),
        valid_pant_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    client.post(
        measurements_url(customer.id),
        valid_pant_payload(),
        content_type="application/json",
        **_auth(staff),
    )

    current = client.get(
        f"{measurements_url(customer.id)}?current=true", **_auth(staff)
    )
    by_garment = {item["garment_type"]: item for item in current.json()}
    assert set(by_garment) == {"SHIRT", "PANT"}
    assert by_garment["SHIRT"]["version"] == 1
    assert by_garment["PANT"]["version"] == 2


def test_update_creates_new_version_and_keeps_old(client, staff, customer):
    first = client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    ).json()

    payload = valid_shirt_payload()
    payload["shirt_length"] = 31.0
    response = client.patch(
        measurement_detail_url(first["id"]),
        payload,
        content_type="application/json",
        **_auth(staff),
    )

    assert response.status_code == 201
    updated = response.json()
    assert updated["version"] == 2
    assert updated["is_current"] is True

    # Old row unchanged and no longer current.
    old = Measurement.objects.get(pk=first["id"])
    assert old.shirt_length == 30.0
    assert old.is_current is False


def test_update_of_historical_version_still_creates_newest(client, staff, customer):
    first = client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    ).json()
    second_payload = valid_shirt_payload()
    second_payload["chest_circumference"] = 42.0
    second = client.post(
        measurements_url(customer.id),
        second_payload,
        content_type="application/json",
        **_auth(staff),
    ).json()

    # Edit the *historical* v1: the newest version must be v3.
    payload = valid_shirt_payload()
    payload["chest_circumference"] = 43.0
    response = client.patch(
        measurement_detail_url(first["id"]),
        payload,
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    assert response.json()["version"] == 3
    assert response.json()["is_current"] is True

    history = client.get(measurements_url(customer.id), **_auth(staff))
    versions = _get_history_versions(history)
    assert versions == [(1, False), (2, False), (3, True)]
    assert second["chest_circumference"] == 42.0


def test_list_is_ordered_by_garment_then_version(client, staff, customer):
    client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    client.post(
        measurements_url(customer.id),
        valid_pant_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    )

    history = client.get(measurements_url(customer.id), **_auth(staff))
    order = [(item["garment_type"], item["version"]) for item in history.json()]
    assert order == [("PANT", 1), ("SHIRT", 1), ("SHIRT", 2)]


def test_historical_version_is_still_retrievable(client, staff, customer):
    first = client.post(
        measurements_url(customer.id),
        valid_shirt_payload(),
        content_type="application/json",
        **_auth(staff),
    ).json()
    payload = valid_shirt_payload()
    payload["chest_circumference"] = 42.0
    client.post(
        measurements_url(customer.id),
        payload,
        content_type="application/json",
        **_auth(staff),
    )

    response = client.get(measurement_detail_url(first["id"]), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["version"] == 1
    assert response.json()["is_current"] is False
    assert response.json()["chest_circumference"] == 40.0
