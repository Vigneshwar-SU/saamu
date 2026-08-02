"""Reusable role-based permission classes for the Saamu Tailors API.

Backend authorization is authoritative: permissions are derived from the
authenticated database user's ``role`` field, never from values supplied by
the frontend. These classes are intentionally few and generic so future
business APIs can be protected without rewriting the authorization layer.

Role model (Phase 2):
- ``IsOwner``        -> only OWNER
- ``IsStaffRole``    -> only STAFF (operational management role)
- ``IsOwnerOrStaff`` -> any authenticated user with a valid application role

Note: application ``STAFF`` is unrelated to Django's ``is_staff`` flag.
"""

from rest_framework.permissions import BasePermission

from apps.authentication.models import Role


class IsOwner(BasePermission):
    """Allow access only to users whose application role is OWNER."""

    message = "This action is restricted to the Owner."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "role", None) == Role.OWNER
        )


class IsStaffRole(BasePermission):
    """Allow access only to users whose application role is STAFF.

    STAFF is the operational management role for business operations.
    """

    message = "This action is restricted to Staff."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "role", None) == Role.STAFF
        )


class IsOwnerOrStaff(BasePermission):
    """Allow access to any authenticated user with a valid application role.

    Used for read/view operations that both OWNER and STAFF may access.
    """

    message = "Authentication with a valid application role is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in Role.values
        )
