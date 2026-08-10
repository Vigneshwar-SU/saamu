"""Email-based password reset (Phase 22).

Stateless token generation and validation use Django's
``PasswordResetTokenGenerator``: tokens are cryptographically safe, expire
after ``PASSWORD_RESET_TIMEOUT`` seconds, and become invalid automatically when
the user's password, last login or email changes (all are part of the token
digest). Single-use is enforced with a ``PasswordResetToken`` row that stores
only the SHA-256 digest of the token - the raw token is emailed to the user and
never persisted.

Account enumeration is prevented at the endpoint layer: ``issue_password_reset``
returns identically whether or not the email belongs to an account, and every
failure inside ``reset_password`` raises the same generic
``PasswordResetTokenInvalid`` error.
"""

import binascii
import hashlib
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.core.exceptions import ValidationError as DjangoValidationError
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers

from apps.authentication.exceptions import PasswordResetTokenInvalid
from apps.authentication.models import PasswordResetToken, User

password_reset_token_generator = PasswordResetTokenGenerator()

GENERIC_RESET_MESSAGE = (
    "If an account exists for this email address, a password reset link has "
    "been sent."
)

RESET_SUCCESS_MESSAGE = "Your password has been reset successfully."

EMAIL_SUBJECT = "Saamu Tailors — Password Reset Request"

SHOP_NAME = "Saamu Tailors"


def hash_token(token):
    """Return the SHA-256 hex digest of a reset token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _prune_expired_records(user):
    """Delete this user's reset records that can no longer be valid."""
    cutoff = timezone.now() - timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
    PasswordResetToken.objects.filter(user=user, created_at__lt=cutoff).delete()


def issue_password_reset(email):
    """Send a reset link if the email belongs to an active account.

    Returns ``None`` whether or not an account exists; callers must always
    return the generic response so account existence is never revealed.
    """
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        return
    _prune_expired_records(user)
    token = password_reset_token_generator.make_token(user)
    PasswordResetToken.objects.create(user=user, token_hash=hash_token(token))
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{uidb64}/{token}"
    send_password_reset_email(user, reset_url)


def send_password_reset_email(user, reset_url):
    """Send the branded HTML reset email with a plain-text fallback."""
    context = {
        "shop_name": SHOP_NAME,
        "reset_url": reset_url,
        "timeout_minutes": settings.PASSWORD_RESET_TIMEOUT // 60,
    }
    text_body = render_to_string("authentication/password_reset_email.txt", context)
    html_body = render_to_string("authentication/password_reset_email.html", context)
    message = mail.EmailMultiAlternatives(
        subject=EMAIL_SUBJECT,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send()


def _resolve_user(uidb64):
    """Decode and return the active user referenced by ``uidb64``.

    Returns ``None`` for any malformed/unknown value so callers raise the
    generic token error without leaking whether the user exists.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
    except (TypeError, ValueError, binascii.Error, UnicodeDecodeError):
        return None
    if not uid.isdigit():
        return None
    return User.objects.filter(pk=uid, is_active=True).first()


def reset_password(uidb64, token, new_password):
    """Validate the reset link and apply the new password (single-use).

    Raises ``PasswordResetTokenInvalid`` for any unusable link (malformed uid,
    unknown user, invalid/expired/used token) and a DRF ``ValidationError``
    with field-level messages when the new password fails the configured
    validators. The token is only consumed after the password passes
    validation, so a failed attempt never burns a valid link.
    """
    user = _resolve_user(uidb64)
    if user is None:
        raise PasswordResetTokenInvalid()
    if not password_reset_token_generator.check_token(user, token):
        raise PasswordResetTokenInvalid()
    record = (
        PasswordResetToken.objects.filter(
            user=user, token_hash=hash_token(token), used=False
        )
        .order_by("-created_at")
        .first()
    )
    if record is None:
        raise PasswordResetTokenInvalid()

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        messages = exc.messages if hasattr(exc, "messages") else [str(exc)]
        raise serializers.ValidationError({"new_password": messages}) from exc

    record.used = True
    record.used_at = timezone.now()
    record.save(update_fields=["used", "used_at", "updated_at"])

    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
