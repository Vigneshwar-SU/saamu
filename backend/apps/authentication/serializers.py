"""Serializers for authentication endpoints.

Login is intentionally a public entry point. Every other auth endpoint
requires authentication (``/me/``, ``/logout/``) or a valid refresh token
(``/refresh/``).
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from apps.authentication.exceptions import InvalidCredentials
from apps.authentication.models import User


class UserSerializer(serializers.ModelSerializer):
    """Public representation of an authenticated user.

    Deliberately excludes passwords, hashes, and any sensitive fields.
    """

    class Meta:
        model = User
        fields = ("id", "username", "role", "is_active")
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    """Validate credentials and issue JWT access/refresh tokens."""

    username = serializers.CharField(max_length=150, trim_whitespace=False)
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if user is None:
            # Safe message: identical whether the username is unknown or the
            # password is wrong, so account existence is never revealed.
            raise InvalidCredentials("Invalid username or password.")

        refresh = RefreshToken.for_user(user)
        attrs["user"] = user
        attrs["access"] = str(refresh.access_token)
        attrs["refresh"] = str(refresh)
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Validate the provided refresh token and blacklist it."""

    refresh = serializers.CharField()

    def validate(self, attrs):
        token_value = attrs.get("refresh")
        try:
            token = RefreshToken(token_value)
            token.blacklist()
        except TokenError as exc:
            raise serializers.ValidationError(
                {"refresh": "Refresh token is invalid or has already been blacklisted."}
            ) from exc
        return attrs
