import pytest
from django.core.exceptions import ValidationError

from apps.authentication.models import Role, User
from apps.authentication.tests.helpers import make_user

pytestmark = pytest.mark.django_db


def test_owner_role_can_be_assigned():
    user = make_user(username="owner_user", role=Role.OWNER)
    assert user.role == "OWNER"
    assert user.role == Role.OWNER


def test_staff_role_can_be_assigned():
    user = make_user(username="staff_user", role=Role.STAFF)
    assert user.role == "STAFF"
    assert user.role == Role.STAFF


def test_exactly_two_application_roles_exist():
    assert set(Role.values) == {"OWNER", "STAFF"}


def test_invalid_role_is_rejected():
    user = User(username="invalid_role_user", role="MANAGER")
    with pytest.raises(ValidationError):
        user.full_clean()


def test_default_role_is_staff():
    user = make_user(username="default_role_user")
    assert user.role == Role.STAFF


def test_superuser_does_not_create_third_application_role():
    superuser = User.objects.create_superuser(
        username="root", password="test-password-123"
    )
    assert superuser.is_superuser is True
    assert superuser.role in Role.values
    assert superuser.role not in ("SUPERUSER", "ADMIN")


def test_django_is_staff_is_independent_of_application_role():
    staff_role_user = make_user(username="staff_flags", role=Role.STAFF)
    assert staff_role_user.is_staff is False
    assert staff_role_user.role == Role.STAFF

    owner_role_user = make_user(username="owner_flags", role=Role.OWNER)
    assert owner_role_user.role == Role.OWNER
    owner_role_user.is_staff = True
    owner_role_user.is_superuser = True
    owner_role_user.save()
    assert owner_role_user.role == Role.OWNER
    assert owner_role_user.is_staff is True
