import pytest

from apps.authentication.models import Role
from apps.authentication.tests.helpers import (
    make_user,
    me_url,
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


def test_access_token_works(client):
    make_user(username="owner", role=Role.OWNER, password=PASSWORD)
    tokens = _login(client, "owner", PASSWORD)
    response = client.get(me_url(), HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert response.status_code == 200
    assert response.json()["username"] == "owner"


def test_invalid_access_token_is_rejected(client):
    response = client.get(me_url(), HTTP_AUTHORIZATION="Bearer not-a-real-token")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "token_not_valid"


def test_refresh_creates_valid_access_token(client):
    make_user(username="staff", role=Role.STAFF, password=PASSWORD)
    tokens = _login(client, "staff", PASSWORD)
    refresh_response = client.post(
        refresh_url(),
        {"refresh": tokens["refresh"]},
        content_type="application/json",
    )
    assert refresh_response.status_code == 200
    new_access = refresh_response.json()["access"]
    me_response = client.get(me_url(), HTTP_AUTHORIZATION=f"Bearer {new_access}")
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "staff"


def test_invalid_refresh_token_is_rejected(client):
    response = client.post(
        refresh_url(), {"refresh": "invalid"}, content_type="application/json"
    )
    assert response.status_code == 401
    assert response.json()["success"] is False
