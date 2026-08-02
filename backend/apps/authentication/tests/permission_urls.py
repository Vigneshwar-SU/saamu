"""Test-only URL configuration for exercising permission classes.

Not part of the application's real routing. It mounts thin generic views
behind the Phase 2 permission classes so authorization can be tested without
inventing fake business CRUD.
"""

from django.urls import include, path
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsOwner, IsOwnerOrStaff, IsStaffRole


class StaffOnlyView(APIView):
    """Protected mutation-style endpoint: STAFF role only."""

    permission_classes = [IsStaffRole]

    def post(self, request, *args, **kwargs):
        return Response({"ok": True})


class OwnerOnlyView(APIView):
    """View restricted to OWNER role only."""

    permission_classes = [IsOwner]

    def get(self, request, *args, **kwargs):
        return Response({"ok": True})


class OwnerOrStaffView(APIView):
    """Read-style endpoint: any authenticated user with a valid role."""

    permission_classes = [IsOwnerOrStaff]

    def get(self, request, *args, **kwargs):
        return Response({"ok": True})


class AuthenticatedOnlyView(APIView):
    """Any authenticated user (regardless of role)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({"ok": True})


urlpatterns = [
    path("", include("apps.authentication.urls")),
    path("_test/staff-only/", StaffOnlyView.as_view()),
    path("_test/owner-only/", OwnerOnlyView.as_view()),
    path("_test/owner-or-staff/", OwnerOrStaffView.as_view()),
    path("_test/authenticated-only/", AuthenticatedOnlyView.as_view()),
]
