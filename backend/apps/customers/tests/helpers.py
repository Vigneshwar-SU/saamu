"""Shared helpers for customer & measurement tests."""

from apps.authentication.models import Role
from apps.authentication.tests.helpers import auth_header, make_user

PASSWORD = "test-password-123"


def customer_list_url():
    return "/api/v1/customers/"


def customer_detail_url(customer_id):
    return f"/api/v1/customers/{customer_id}/"


def customer_archive_url(customer_id):
    return f"/api/v1/customers/{customer_id}/archive/"


def customer_restore_url(customer_id):
    return f"/api/v1/customers/{customer_id}/restore/"


def measurements_url(customer_id):
    return f"/api/v1/customers/{customer_id}/measurements/"


def measurement_detail_url(measurement_id):
    return f"/api/v1/measurements/{measurement_id}/"


def create_customer(full_name="Ravi Kumar", mobile_number="9876543210", **kwargs):
    from apps.customers.models import Customer

    defaults = {"full_name": full_name, "mobile_number": mobile_number}
    defaults.update(kwargs)
    return Customer.objects.create(**defaults)


def valid_customer_payload():
    return {
        "full_name": "Ravi Kumar",
        "mobile_number": "9876543210",
        "alternate_mobile_number": "",
        "address": "12, MG Road, Bengaluru",
        "notes": "Prefers morning stitching.",
    }


def valid_shirt_payload():
    return {
        "garment_type": "SHIRT",
        "neck_circumference": 15.5,
        "chest_circumference": 40.0,
        "waist_circumference": 34.0,
        "shoulder_width": 18.5,
        "sleeve_length": 25.0,
        "sleeve_circumference": 14.0,
        "cuff_circumference": 9.5,
        "shirt_length": 30.0,
        "notes": "Regular fit shirt.",
    }


def valid_pant_payload():
    return {
        "garment_type": "PANT",
        "waist_circumference": 34.0,
        "hip_circumference": 40.0,
        "length": 41.0,
        "thigh_circumference": 23.0,
        "knee_circumference": 18.0,
        "bottom_circumference": 12.0,
        "notes": "Straight fit pant.",
    }


def make_owner(username="owner_c"):
    return make_user(username=username, role=Role.OWNER, password=PASSWORD)


def make_staff(username="staff_c"):
    return make_user(username=username, role=Role.STAFF, password=PASSWORD)
