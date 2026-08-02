import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.authentication.models import Role, User

pytestmark = pytest.mark.django_db


def test_create_owner_creates_owner_role_user():
    call_command("create_owner", username="the_owner", password="secret-pass-123")
    user = User.objects.get(username="the_owner")
    assert user.role == Role.OWNER
    assert user.is_active is True
    assert user.is_superuser is False


def test_create_owner_with_superuser_flag():
    call_command(
        "create_owner",
        username="admin_owner",
        password="secret-pass-123",
        superuser=True,
    )
    user = User.objects.get(username="admin_owner")
    assert user.role == Role.OWNER
    assert user.is_superuser is True
    assert user.is_staff is True


def test_create_owner_promotes_existing_user_to_owner():
    User.objects.create_user(
        username="existing", password="secret-pass-123", role=Role.STAFF
    )
    call_command("create_owner", username="existing", password="other-pass-123")
    user = User.objects.get(username="existing")
    assert user.role == Role.OWNER


def test_create_owner_requires_password():
    with pytest.raises(CommandError):
        call_command("create_owner", username="owner")
