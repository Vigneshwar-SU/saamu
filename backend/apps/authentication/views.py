"""Authentication views.

Endpoints:
- POST /api/v1/auth/login/     (public)
- POST /api/v1/auth/refresh/   (public; simplejwt TokenRefreshView)
- GET  /api/v1/auth/me/        (authenticated)
- POST /api/v1/auth/logout/    (authenticated; blacklists the refresh token)
- POST /api/v1/auth/password-reset/         (public, rate-limited)
- POST /api/v1/auth/password-reset/confirm/ (public, rate-limited)
"""

from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.authentication.password_reset import (
    GENERIC_RESET_MESSAGE,
    RESET_SUCCESS_MESSAGE,
    issue_password_reset,
    reset_password,
)
from apps.authentication.serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserSerializer,
)


class LoginView(APIView):
    """Issue JWT access/refresh tokens for valid OWNER/STAFF credentials."""

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(
            {
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(data["user"]).data,
            },
            status=http_status.HTTP_200_OK,
        )


class MeView(APIView):
    """Return the authenticated user's public profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            UserSerializer(request.user).data, status=http_status.HTTP_200_OK
        )


class LogoutView(APIView):
    """Invalidate the supplied refresh token by blacklisting it."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"success": True, "message": "Logged out successfully."},
            status=http_status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    """Request a password reset link (public, rate-limited).

    Always returns the same generic success response whether or not the email
    belongs to an account, so account existence is never revealed. Emails are
    only sent for active accounts (OWNER and STAFF alike).
    """

    permission_classes = []
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_request"

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issue_password_reset(serializer.validated_data["email"])
        return Response(
            {"success": True, "message": GENERIC_RESET_MESSAGE},
            status=http_status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Apply a new password for a valid, unused, unexpired reset token (public).

    Any unusable link (malformed uid, unknown user, invalid/expired/used
    token) returns the same generic ``invalid_reset_token`` error so nothing
    about the account or token internals is revealed.
    """

    permission_classes = []
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_confirm"

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        reset_password(data["uid"], data["token"], data["new_password"])
        return Response(
            {"success": True, "message": RESET_SUCCESS_MESSAGE},
            status=http_status.HTTP_200_OK,
        )
