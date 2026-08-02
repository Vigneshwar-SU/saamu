"""Shared helpers for authentication tests."""

from apps.authentication.models import Role, User


def make_user(
    username="staff_user",
    role=Role.STAFF,
    password="test-password-123",
    is_active=True,
):
    """Create a user with a specific application role."""
    return User.objects.create_user(
        username=username,
        password=password,
        role=role,
        is_active=is_active,
    )


def login_url():
    return "/api/v1/auth/login/"


def me_url():
    return "/api/v1/auth/me/"


def logout_url():
    return "/api/v1/auth/logout/"


def refresh_url():
    return "/api/v1/auth/refresh/"


def auth_header(user):
    from rest_framework_simplejwt.tokens import RefreshToken

    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}
