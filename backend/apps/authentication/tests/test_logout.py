import pytest

from apps.authentication.models import Role
from apps.authentication.tests.helpers import (
    make_user,
    refresh_url,
)

pytestmark = pytest.mark.django_db

PASSWORD = "test-password-123"


def _login(client, username, password):
    response = client.post(
        "/api/v1/auth/login/",
        {"username": username, "password": password},
        content_type="application/json",
    )
    assert response.status_code == 200
    return response.json()


def test_logout_succeeds_and_returns_confirmation(client):
    make_user(username="staff", role=Role.STAFF, password=PASSWORD)
    tokens = _login(client, "staff", PASSWORD)
    response = client.post(
        "/api/v1/auth/logout/",
        {"refresh": tokens["refresh"]},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_blacklisted_refresh_token_cannot_be_reused(client):
    make_user(username="staff", role=Role.STAFF, password=PASSWORD)
    tokens = _login(client, "staff", PASSWORD)
    response = client.post(
        "/api/v1/auth/logout/",
        {"refresh": tokens["refresh"]},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )
    assert response.status_code == 200

    reuse = client.post(
        refresh_url(), {"refresh": tokens["refresh"]}, content_type="application/json"
    )
    assert reuse.status_code == 401
    assert reuse.json()["success"] is False


def test_logout_requires_authentication(client):
    make_user(username="staff", role=Role.STAFF, password=PASSWORD)
    tokens = _login(client, "staff", PASSWORD)
    response = client.post(
        "/api/v1/auth/logout/",
        {"refresh": tokens["refresh"]},
        content_type="application/json",
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_logout_rejects_invalid_refresh_body(client):
    make_user(username="staff", role=Role.STAFF, password=PASSWORD)
    tokens = _login(client, "staff", PASSWORD)
    response = client.post(
        "/api/v1/auth/logout/",
        {"refresh": "garbage"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
