"""Tailor CRUD, search, scope filtering and archive/restore tests."""

import pytest

from apps.customers.tests.helpers import auth_header
from apps.tailors.models import Tailor
from apps.tailors.tests.helpers import (
    create_tailor,
    make_staff,
    tailor_archive_url,
    tailor_restore_url,
    tailor_url,
    tailors_url,
    valid_tailor_payload,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def test_staff_can_create_tailor(client, staff):
    response = client.post(
        tailors_url(),
        valid_tailor_payload(),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Arun Stitcher"
    assert data["mobile_number"] == "9123456780"
    assert data["is_active"] is True


def test_tailor_name_is_required(client, staff):
    response = client.post(
        tailors_url(), {"name": ""}, content_type="application/json", **_auth(staff)
    )
    assert response.status_code == 400
    assert "name" in response.json()["error"]["details"]


def test_tailor_name_too_long_rejected(client, staff):
    response = client.post(
        tailors_url(),
        {"name": "X" * 201},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_invalid_mobile_number_rejected(client, staff):
    response = client.post(
        tailors_url(),
        valid_tailor_payload(mobile_number="12345"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400


def test_blank_mobile_number_allowed(client, staff):
    response = client.post(
        tailors_url(),
        valid_tailor_payload(mobile_number=""),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201


def test_staff_can_update_tailor(client, staff):
    tailor = create_tailor()
    response = client.patch(
        tailor_url(tailor.id),
        {"name": "Renamed Stitcher"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Stitcher"


def test_list_defaults_to_active(client, staff):
    create_tailor("Active One", is_active=True)
    create_tailor("Archived One", is_active=False)
    response = client.get(tailors_url(), **_auth(staff))
    assert response.status_code == 200
    names = [t["name"] for t in response.json()["results"]]
    assert "Active One" in names
    assert "Archived One" not in names


def test_list_scope_archived(client, staff):
    create_tailor("Active One", is_active=True)
    create_tailor("Archived One", is_active=False)
    response = client.get(tailors_url(), {"scope": "archived"}, **_auth(staff))
    names = [t["name"] for t in response.json()["results"]]
    assert "Archived One" in names
    assert "Active One" not in names


def test_list_scope_all(client, staff):
    create_tailor("Active One", is_active=True)
    create_tailor("Archived One", is_active=False)
    response = client.get(tailors_url(), {"scope": "all"}, **_auth(staff))
    names = [t["name"] for t in response.json()["results"]]
    assert "Archived One" in names
    assert "Active One" in names


def test_list_invalid_scope_rejected(client, staff):
    response = client.get(tailors_url(), {"scope": "bogus"}, **_auth(staff))
    assert response.status_code == 400


def test_list_search_by_name(client, staff):
    create_tailor("Arun Stitcher")
    create_tailor("Balu Weaver")
    response = client.get(tailors_url(), {"search": "arun"}, **_auth(staff))
    names = [t["name"] for t in response.json()["results"]]
    assert "Arun Stitcher" in names
    assert "Balu Weaver" not in names


def test_list_search_by_mobile(client, staff):
    create_tailor("Arun Stitcher", mobile_number="9123456780")
    response = client.get(tailors_url(), {"search": "91234"}, **_auth(staff))
    names = [t["name"] for t in response.json()["results"]]
    assert "Arun Stitcher" in names


def test_archive_tailor(client, staff):
    tailor = create_tailor()
    response = client.post(tailor_archive_url(tailor.id), **_auth(staff))
    assert response.status_code == 200
    tailor.refresh_from_db()
    assert tailor.is_active is False


def test_archive_already_archived_rejected(client, staff):
    tailor = create_tailor(is_active=False)
    response = client.post(tailor_archive_url(tailor.id), **_auth(staff))
    assert response.status_code == 400


def test_restore_tailor(client, staff):
    tailor = create_tailor(is_active=False)
    response = client.post(tailor_restore_url(tailor.id), **_auth(staff))
    assert response.status_code == 200
    tailor.refresh_from_db()
    assert tailor.is_active is True


def test_restore_active_tailor_rejected(client, staff):
    tailor = create_tailor(is_active=True)
    response = client.post(tailor_restore_url(tailor.id), **_auth(staff))
    assert response.status_code == 400


def test_no_delete_endpoint(client, staff):
    tailor = create_tailor()
    response = client.delete(tailor_url(tailor.id), **_auth(staff))
    assert response.status_code == 405
    assert Tailor.objects.filter(pk=tailor.pk).exists()


def test_tailors_are_never_physically_deleted_on_archive(client, staff):
    tailor = create_tailor()
    client.post(tailor_archive_url(tailor.id), **_auth(staff))
    assert Tailor.objects.filter(pk=tailor.pk).exists()
