"""Authentication-specific exceptions."""

from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    """Returned when a login attempt fails.

    A distinct class (rather than ``AuthenticationFailed``) so that DRF does
    not rewrite the response to 403 when a public endpoint has no
    ``WWW-Authenticate`` header to offer. The message is deliberately
    identical for unknown usernames and wrong passwords so account existence
    is never revealed.
    """

    status_code = 401
    default_code = "authentication_failed"
    default_detail = "Invalid username or password."


class PasswordResetTokenInvalid(APIException):
    """Returned when a password reset link is unusable.

    A single generic message covers every failure (malformed uid, unknown
    user, invalid/expired/used token) so the response never reveals whether an
    account exists, leaks token internals, or leaks user identifiers.
    """

    status_code = 400
    default_code = "invalid_reset_token"
    default_detail = "The password reset link is invalid or has expired."
