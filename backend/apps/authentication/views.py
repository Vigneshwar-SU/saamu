"""Authentication views.

Endpoints:
- POST /api/v1/auth/login/     (public)
- POST /api/v1/auth/refresh/   (public; simplejwt TokenRefreshView)
- GET  /api/v1/auth/me/        (authenticated)
- POST /api/v1/auth/logout/    (authenticated; blacklists the refresh token)
"""

from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.serializers import (
    LoginSerializer,
    LogoutSerializer,
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
