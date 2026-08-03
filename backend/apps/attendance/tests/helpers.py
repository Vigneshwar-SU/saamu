"""Shared helpers for attendance tests."""

from datetime import date

from apps.attendance.models import Attendance
from apps.customers.tests.helpers import make_owner, make_staff  # noqa: F401


def attendance_list_url():
    return "/api/v1/attendance/"


def attendance_detail_url(record_id):
    return f"/api/v1/attendance/{record_id}/"


def create_attendance(
    tailor, attendance_date=None, status=Attendance.Status.PRESENT, **kwargs
):
    defaults = {
        "tailor": tailor,
        "attendance_date": attendance_date or date.today(),
        "status": status,
    }
    defaults.update(kwargs)
    return Attendance.objects.create(**defaults)
