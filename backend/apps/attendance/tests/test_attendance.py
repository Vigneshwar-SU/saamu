"""Attendance CRUD, RBAC, validation and filtering tests."""

from datetime import date, timedelta

import pytest

from apps.attendance.models import Attendance
from apps.attendance.tests.helpers import (
    attendance_detail_url,
    attendance_list_url,
    create_attendance,
    make_owner,
    make_staff,
)
from apps.customers.tests.helpers import auth_header
from apps.tailors.tests.helpers import create_tailor

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _payload(tailor, **extra):
    payload = {
        "tailor": tailor.id,
        "attendance_date": str(date.today()),
        "status": "PRESENT",
        "notes": "Full day",
    }
    payload.update(extra)
    return payload


def test_anonymous_denied(client):
    response = client.get(attendance_list_url())
    assert response.status_code == 401
    response = client.post(
        attendance_list_url(),
        {"tailor": 1, "attendance_date": str(date.today()), "status": "PRESENT"},
        content_type="application/json",
    )
    assert response.status_code == 401


def test_owner_can_read(client, owner):
    tailor = create_tailor()
    create_attendance(tailor)
    response = client.get(attendance_list_url(), **_auth(owner))
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_owner_mutation_forbidden(client, owner):
    tailor = create_tailor()
    response = client.post(
        attendance_list_url(),
        _payload(tailor),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403
    record = create_attendance(tailor)
    response = client.patch(
        attendance_detail_url(record.id),
        {"status": "ABSENT"},
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403


def test_staff_can_create(client, staff):
    tailor = create_tailor()
    response = client.post(
        attendance_list_url(),
        _payload(tailor),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PRESENT"
    assert data["tailor"]["id"] == tailor.id
    assert data["marked_by_name"] == staff.username


def test_all_statuses_created(client, staff):
    tailor = create_tailor()
    for index, status in enumerate(Attendance.Status.values):
        day = date.today() - timedelta(days=index)
        response = client.post(
            attendance_list_url(),
            _payload(tailor, attendance_date=str(day), status=status),
            content_type="application/json",
            **_auth(staff),
        )
        assert response.status_code == 201
        assert response.json()["status"] == status


def test_duplicate_tailor_date_rejected(client, staff):
    tailor = create_tailor()
    response = client.post(
        attendance_list_url(),
        _payload(tailor),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 201

    response = client.post(
        attendance_list_url(),
        _payload(tailor),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "attendance_date" in response.json()["error"]["details"]


def test_duplicate_rejected_via_direct_orm():
    tailor = create_tailor()
    create_attendance(tailor)
    with pytest.raises(Exception):
        create_attendance(tailor)


def test_staff_can_update(client, staff):
    tailor = create_tailor()
    record = create_attendance(tailor, status=Attendance.Status.PRESENT)
    response = client.patch(
        attendance_detail_url(record.id),
        {"status": "HALF_DAY", "notes": "Left at noon"},
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HALF_DAY"
    assert data["notes"] == "Left at noon"


def test_invalid_status_rejected(client, staff):
    tailor = create_tailor()
    response = client.post(
        attendance_list_url(),
        _payload(tailor, status="BOGUS"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "status" in response.json()["error"]["details"]


def test_filter_by_tailor(client, staff):
    tailor_a = create_tailor("Tailor A")
    tailor_b = create_tailor("Tailor B")
    create_attendance(tailor_a)
    create_attendance(tailor_b)

    response = client.get(
        attendance_list_url(), {"tailor": tailor_a.id}, **_auth(staff)
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["tailor"]["id"] == tailor_a.id


def test_filter_by_status(client, staff):
    tailor = create_tailor()
    create_attendance(tailor, status=Attendance.Status.PRESENT)
    create_attendance(
        tailor,
        attendance_date=date.today() - timedelta(days=1),
        status=Attendance.Status.ABSENT,
    )

    response = client.get(attendance_list_url(), {"status": "ABSENT"}, **_auth(staff))
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["status"] == "ABSENT"


def test_filter_invalid_status_rejected(client, staff):
    response = client.get(attendance_list_url(), {"status": "BOGUS"}, **_auth(staff))
    assert response.status_code == 400


def test_filter_by_date_range(client, staff):
    tailor = create_tailor()
    create_attendance(tailor, attendance_date=date.today() - timedelta(days=10))
    create_attendance(tailor, attendance_date=date.today() - timedelta(days=2))
    create_attendance(tailor, attendance_date=date.today())

    response = client.get(
        attendance_list_url(),
        {
            "date_from": str(date.today() - timedelta(days=5)),
            "date_to": str(date.today()),
        },
        **_auth(staff),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_historical_records_visible_after_archive(client, staff):
    tailor = create_tailor()
    record = create_attendance(tailor)

    client.post(f"/api/v1/tailors/{tailor.id}/archive/", **_auth(staff))

    response = client.get(attendance_detail_url(record.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["tailor"]["is_active"] is False
