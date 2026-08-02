import pytest

from apps.authentication.models import Role
from apps.authentication.tests.helpers import (
    make_user,
    me_url,
)

pytestmark = pytest.mark.django_db

PASSWORD = "test-password-123"
EXPECTED_FIELDS = {"id", "username", "role", "is_active"}


def _login_and_token(client, username, password):
    response = client.post(
        "/api/v1/auth/login/",
        {"username": username, "password": password},
        content_type="application/json",
    )
    assert response.status_code == 200
    return response.json()["access"]


def test_authenticated_user_can_access_me(client):
    make_user(username="owner", role=Role.OWNER, password=PASSWORD)
    access = _login_and_token(client, "owner", PASSWORD)
    response = client.get(me_url(), HTTP_AUTHORIZATION=f"Bearer {access}")
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "owner"
    assert body["role"] == "OWNER"
    assert body["is_active"] is True
    assert isinstance(body["id"], int)


def test_anonymous_user_cannot_access_me(client):
    response = client.get(me_url())
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "authentication_required"


def test_me_returns_role(client):
    make_user(username="staff", role=Role.STAFF, password=PASSWORD)
    access = _login_and_token(client, "staff", PASSWORD)
    response = client.get(me_url(), HTTP_AUTHORIZATION=f"Bearer {access}")
    assert response.json()["role"] == "STAFF"


def test_me_excludes_sensitive_fields(client):
    make_user(username="staff", role=Role.STAFF, password=PASSWORD)
    access = _login_and_token(client, "staff", PASSWORD)
    response = client.get(me_url(), HTTP_AUTHORIZATION=f"Bearer {access}")
    body = response.json()
    assert set(body.keys()) == EXPECTED_FIELDS
    assert "password" not in body
    assert all("password" not in key.lower() for key in body)
