import pytest

from apps.authentication.models import Role
from apps.authentication.tests.helpers import (
    login_url,
    make_user,
)

pytestmark = pytest.mark.django_db

PASSWORD = "test-password-123"
EXPECTED_ERROR_MESSAGE = "Invalid username or password."


def _login(client, username, password):
    return client.post(
        login_url(),
        {"username": username, "password": password},
        content_type="application/json",
    )


def test_valid_owner_login_succeeds(client):
    make_user(username="owner", role=Role.OWNER, password=PASSWORD)
    response = _login(client, "owner", PASSWORD)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"access", "refresh", "user"}
    assert data["user"]["username"] == "owner"
    assert data["user"]["role"] == "OWNER"
    assert data["access"]
    assert data["refresh"]


def test_valid_staff_login_succeeds(client):
    make_user(username="staff", role=Role.STAFF, password=PASSWORD)
    response = _login(client, "staff", PASSWORD)
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "STAFF"


def test_invalid_credentials_fail_safely(client):
    make_user(username="owner", role=Role.OWNER, password=PASSWORD)
    response = _login(client, "owner", "wrong-password")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "authentication_failed"
    assert body["error"]["message"] == EXPECTED_ERROR_MESSAGE


def test_invalid_login_does_not_reveal_account_existence(client):
    make_user(username="owner", role=Role.OWNER, password=PASSWORD)
    wrong_password = _login(client, "owner", "wrong-password")
    unknown_user = _login(client, "no_such_user", PASSWORD)
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert (
        wrong_password.json()["error"]["message"]
        == unknown_user.json()["error"]["message"]
    )


def test_login_response_never_exposes_passwords_or_hashes(client):
    make_user(username="owner", role=Role.OWNER, password=PASSWORD)
    response = _login(client, "owner", PASSWORD)
    assert response.status_code == 200
    user_payload = response.json()["user"]
    assert "password" not in user_payload
    assert all("password" not in key.lower() for key in user_payload)


def test_missing_credentials_returns_400(client):
    response = client.post(login_url(), {}, content_type="application/json")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert "details" in body["error"]


def test_inactive_user_cannot_login(client):
    make_user(username="inactive", role=Role.STAFF, password=PASSWORD, is_active=False)
    response = _login(client, "inactive", PASSWORD)
    assert response.status_code == 401
    assert response.json()["error"]["message"] == EXPECTED_ERROR_MESSAGE
