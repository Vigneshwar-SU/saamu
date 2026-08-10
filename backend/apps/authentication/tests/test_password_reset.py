"""Phase 22 email-based password reset tests.

Covers the public request endpoint (identical generic response whether or not
the email exists, real email only for active OWNER/STAFF accounts), the
single-use / expiring token mechanism, the confirm endpoint (password change
only; role and account state preserved), and rate limiting on both public
endpoints.
"""

import re
from datetime import datetime, timedelta

import pytest
from django.core import cache, mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.authentication.models import PasswordResetToken, Role, User
from apps.authentication.password_reset import (
    GENERIC_RESET_MESSAGE,
    hash_token,
    password_reset_token_generator,
)
from apps.authentication.tests.helpers import login_url, make_user

pytestmark = pytest.mark.django_db

REQUEST_URL = "/api/v1/auth/password-reset/"
CONFIRM_URL = "/api/v1/auth/password-reset/confirm/"

PASSWORD = "test-password-123"


@pytest.fixture(autouse=True)
def _test_email_and_throttle(settings):
    """Use the in-memory email backend and reset throttle state per test."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox.clear()
    cache.cache.clear()
    yield


def _make_user(email, username="reset_user", role=Role.STAFF, is_active=True):
    user = make_user(username=username, role=role, password=PASSWORD, is_active=is_active)
    user.email = email
    user.save(update_fields=["email"])
    return user


def _request(client, email):
    return client.post(REQUEST_URL, {"email": email}, content_type="application/json")


def _confirm(client, uid, token, new_password=PASSWORD, confirm_password=None):
    payload = {
        "uid": uid,
        "token": token,
        "new_password": new_password,
        "confirm_password": confirm_password
        if confirm_password is not None
        else new_password,
    }
    return client.post(CONFIRM_URL, payload, content_type="application/json")


def _uidb64(pk):
    return urlsafe_base64_encode(force_bytes(pk))


def _token_and_uid_from_outbox():
    """Return ``(uidb64, token)`` parsed from the reset link in the email."""
    body = mail.outbox[0].body
    match = re.search(r"/reset-password/([^/]+)/([^/\s]+)", body)
    assert match, "reset link not found in the email body"
    return match.group(1), match.group(2)


# ---------------------------------------------------------------------------
# Request endpoint
# ---------------------------------------------------------------------------


def test_request_requires_no_authentication(client):
    response = _request(client, "nobody@example.com")
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": GENERIC_RESET_MESSAGE}


def test_request_for_existing_email_sends_reset_email(client):
    user = _make_user(email="owner@example.com", role=Role.OWNER)
    response = _request(client, "owner@example.com")
    assert response.status_code == 200
    assert response.json()["message"] == GENERIC_RESET_MESSAGE
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.subject == "Saamu Tailors — Password Reset Request"
    assert message.to == ["owner@example.com"]
    uid, token = _token_and_uid_from_outbox()
    assert uid == _uidb64(user.pk)
    assert token
    assert PasswordResetToken.objects.filter(
        user=user, token_hash=hash_token(token), used=False
    ).exists()


def test_request_for_unknown_email_returns_same_generic_response(client):
    response = _request(client, "nobody@example.com")
    assert response.status_code == 200
    assert response.json()["message"] == GENERIC_RESET_MESSAGE
    assert len(mail.outbox) == 0


def test_request_response_identical_for_existing_and_unknown_email(client):
    _make_user(email="known@example.com")
    known = _request(client, "known@example.com")
    unknown = _request(client, "unknown@example.com")
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


def test_request_never_leaks_account_information(client):
    _make_user(email="known@example.com")
    response = _request(client, "known@example.com")
    assert response.json() == {"success": True, "message": GENERIC_RESET_MESSAGE}


def test_request_email_body_contains_reset_link_but_no_password(client):
    _make_user(email="known@example.com")
    _request(client, "known@example.com")
    body = mail.outbox[0].body
    assert "/reset-password/" in body
    assert PASSWORD not in body
    assert "test-password" not in body


def test_request_rejects_malformed_email(client):
    response = _request(client, "not-an-email")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert len(mail.outbox) == 0


def test_request_for_inactive_user_sends_no_email(client):
    _make_user(email="inactive@example.com", is_active=False)
    response = _request(client, "inactive@example.com")
    assert response.status_code == 200
    assert response.json()["message"] == GENERIC_RESET_MESSAGE
    assert len(mail.outbox) == 0


def test_request_for_owner_and_staff_both_send_email(client):
    _make_user(email="owner@example.com", username="owner_user", role=Role.OWNER)
    _make_user(email="staff@example.com", username="staff_user", role=Role.STAFF)
    assert _request(client, "owner@example.com").status_code == 200
    assert _request(client, "staff@example.com").status_code == 200
    assert len(mail.outbox) == 2
    assert {message.to[0] for message in mail.outbox} == {
        "owner@example.com",
        "staff@example.com",
    }


def test_request_email_matches_case_insensitively(client):
    _make_user(email="mixed@example.com")
    response = _request(client, "MIXED@Example.COM")
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["mixed@example.com"]


# ---------------------------------------------------------------------------
# Token behaviour
# ---------------------------------------------------------------------------


def test_confirm_uses_valid_token_and_changes_password(client):
    user = _make_user(email="staff@example.com")
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    response = _confirm(client, uid, token, new_password="new-secure-password-1")
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Your password has been reset successfully.",
    }
    user.refresh_from_db()
    assert user.check_password("new-secure-password-1")
    assert not user.check_password(PASSWORD)
    record = PasswordResetToken.objects.get(user=user)
    assert record.used is True
    assert record.used_at is not None


def test_confirm_with_invalid_token_is_rejected(client):
    user = _make_user(email="staff@example.com")
    _request(client, "staff@example.com")
    uid, _ = _token_and_uid_from_outbox()
    response = _confirm(client, uid, "not-a-valid-token")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_reset_token"
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_confirm_with_malformed_uid_is_rejected(client):
    _make_user(email="staff@example.com")
    response = _confirm(client, "%%%not-base64%%%", "anything")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_reset_token"


def test_confirm_with_nonexistent_uid_is_rejected(client):
    response = _confirm(client, _uidb64(999999), "whatever-token")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_reset_token"


def test_confirm_with_non_numeric_uid_is_rejected(client):
    response = _confirm(client, _uidb64("not-a-number"), "whatever-token")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_reset_token"


def test_confirm_with_expired_token_is_rejected(client, monkeypatch):
    user = _make_user(email="staff@example.com")
    now = datetime.now()
    with monkeypatch.context() as m:
        m.setattr(
            password_reset_token_generator,
            "_now",
            lambda: now - timedelta(hours=1),
        )
        token = password_reset_token_generator.make_token(user)
    PasswordResetToken.objects.create(user=user, token_hash=hash_token(token))
    response = _confirm(client, _uidb64(user.pk), token)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_reset_token"
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_confirm_token_is_single_use(client):
    user = _make_user(email="staff@example.com")
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    first = _confirm(client, uid, token, new_password="first-new-password-1")
    assert first.status_code == 200
    second = _confirm(client, uid, token, new_password="second-new-password-1")
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "invalid_reset_token"
    user.refresh_from_db()
    assert user.check_password("first-new-password-1")
    assert not user.check_password("second-new-password-1")


def test_confirm_token_invalidated_after_password_change(client):
    user = _make_user(email="staff@example.com")
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    user.set_password("changed-outside-1")
    user.save(update_fields=["password"])
    response = _confirm(client, uid, token)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_reset_token"
    user.refresh_from_db()
    assert user.check_password("changed-outside-1")


# ---------------------------------------------------------------------------
# Confirm endpoint
# ---------------------------------------------------------------------------


def test_confirm_requires_no_authentication(client):
    _make_user(email="staff@example.com")
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    response = _confirm(client, uid, token, new_password="new-secure-password-1")
    assert response.status_code == 200


def test_confirm_password_mismatch(client):
    user = _make_user(email="staff@example.com")
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    response = _confirm(
        client,
        uid,
        token,
        new_password="new-secure-password-1",
        confirm_password="different-password-1",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "confirm_password" in body["error"]["details"]
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_confirm_weak_password_rejected_and_token_not_consumed(client):
    user = _make_user(email="staff@example.com")
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    response = _confirm(client, uid, token, new_password="12345678")
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "new_password" in body["error"]["details"]
    record = PasswordResetToken.objects.get(user=user)
    assert record.used is False
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_confirm_empty_password_rejected(client):
    _make_user(email="staff@example.com")
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    response = _confirm(client, uid, token, new_password="", confirm_password="")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_confirm_preserves_role_username_and_active_status(client):
    user = _make_user(
        email="staff@example.com",
        username="original_user",
        role=Role.STAFF,
    )
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    response = _confirm(client, uid, token, new_password="new-secure-password-1")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.role == Role.STAFF
    assert user.username == "original_user"
    assert user.is_active is True


def test_owner_reset_keeps_owner_role(client):
    user = _make_user(email="owner@example.com", username="owner_user", role=Role.OWNER)
    _request(client, "owner@example.com")
    uid, token = _token_and_uid_from_outbox()
    response = _confirm(client, uid, token, new_password="new-secure-password-1")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.role == Role.OWNER
    assert user.check_password("new-secure-password-1")


def test_new_password_works_and_old_password_fails(client):
    user = _make_user(email="staff@example.com", username="staff_user")
    _request(client, "staff@example.com")
    uid, token = _token_and_uid_from_outbox()
    _confirm(client, uid, token, new_password="new-secure-password-1")
    user.refresh_from_db()
    assert user.check_password("new-secure-password-1")
    assert not user.check_password(PASSWORD)

    ok = client.post(
        login_url(),
        {"username": "staff_user", "password": "new-secure-password-1"},
        content_type="application/json",
    )
    assert ok.status_code == 200
    assert ok.json()["user"]["role"] == "STAFF"

    bad = client.post(
        login_url(),
        {"username": "staff_user", "password": PASSWORD},
        content_type="application/json",
    )
    assert bad.status_code == 401


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_request_endpoint_rate_limited(client):
    _make_user(email="staff@example.com")
    for _ in range(5):
        assert _request(client, "staff@example.com").status_code == 200
    response = _request(client, "staff@example.com")
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "throttled"
