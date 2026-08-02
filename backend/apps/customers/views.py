"""Customer and measurement API views.

Permission model (backend is authoritative; frontend role values are never
trusted):

- Read (list/search/detail/measurement view) -> OWNER or STAFF.
- Mutations (create/update/archive/restore, measurement create/update) -> STAFF only.

Customer IDs are stable internal primary keys. The `list` endpoint applies
search + status filtering; `retrieve` (and the archive/restore actions) always
operate on the full set so archived customers remain viewable and restorable.
"""

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.customers.models import Customer, Measurement
from apps.customers.serializers import CustomerSerializer, MeasurementSerializer

CUSTOMER_MUTATION_ACTIONS = {"create", "update", "partial_update", "archive", "restore"}


class IsOwnerOrStaffReadOnly(BasePermission):
    """Allow reads for OWNER/STAFF and mutations for STAFF only.

    Combines the existing Phase 2 permission classes so every business view
    enforces: OWNER = view-only, STAFF = operational management.
    """

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return IsOwnerOrStaff().has_permission(request, view)
        return IsStaffRole().has_permission(request, view)


class CustomerViewSet(viewsets.ModelViewSet):
    """Customers: list/search/filter/detail for OWNER+STAFF; create/update/
    archive/restore for STAFF only."""

    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.action in CUSTOMER_MUTATION_ACTIONS:
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_queryset(self):
        qs = Customer.objects.all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        """Search (name/mobile/alternate/id) and active/archived filtering.

        ``?status=active`` (default), ``?status=archived``, ``?status=all``.
        Search is case-insensitive for text fields; a numeric search also
        matches the customer ID.
        """
        status = self.request.query_params.get("status")
        if status == "archived":
            qs = qs.filter(is_active=False)
        elif status == "all":
            qs = qs
        else:
            qs = qs.filter(is_active=True)

        search = (self.request.query_params.get("search") or "").strip()
        if search:
            lookup = (
                models.Q(full_name__icontains=search)
                | models.Q(mobile_number__icontains=search)
                | models.Q(alternate_mobile_number__icontains=search)
            )
            if search.isdigit():
                lookup |= models.Q(pk=int(search))
            qs = qs.filter(lookup)
        return qs

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        customer = self.get_object()
        if not customer.is_active:
            return Response(
                {"success": True, "message": "Customer is already archived."},
                status=http_status.HTTP_200_OK,
            )
        customer.is_active = False
        customer.save(update_fields=["is_active", "updated_at"])
        return Response(
            {"success": True, "message": "Customer archived successfully."},
            status=http_status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        customer = self.get_object()
        if customer.is_active:
            return Response(
                {"success": True, "message": "Customer is already active."},
                status=http_status.HTTP_200_OK,
            )
        customer.is_active = True
        customer.save(update_fields=["is_active", "updated_at"])
        return Response(
            {"success": True, "message": "Customer restored successfully."},
            status=http_status.HTTP_200_OK,
        )


class CustomerMeasurementListCreateView(APIView):
    """GET list of a customer's measurements (history) and POST a new version.

    List ordering follows the model: garment type, then version (the current
    measurement is the highest version of each garment type). Supports
    ``?current=true`` to return only current measurements.
    """

    permission_classes = [IsOwnerOrStaffReadOnly]

    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, pk=customer_id)
        qs = Measurement.objects.filter(customer=customer).select_related("customer")
        if request.query_params.get("current") == "true":
            qs = qs.filter(is_current=True)
        serializer = MeasurementSerializer(qs, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    def post(self, request, customer_id):
        customer = get_object_or_404(Customer, pk=customer_id)
        serializer = MeasurementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(customer=customer)
        return Response(
            MeasurementSerializer(instance).data,
            status=http_status.HTTP_201_CREATED,
        )


class MeasurementDetailView(APIView):
    """GET a single measurement (any historical version) and PATCH to record a
    new current version.

    PATCH follows the immutable-records strategy: it never mutates the existing
    row; it creates a new current version for the same (customer, garment_type)
    using the supplied values. The garment type of a measurement cannot change.
    """

    permission_classes = [IsOwnerOrStaffReadOnly]

    def get(self, request, pk):
        measurement = get_object_or_404(Measurement, pk=pk)
        return Response(
            MeasurementSerializer(measurement).data, status=http_status.HTTP_200_OK
        )

    def patch(self, request, pk):
        existing = get_object_or_404(Measurement, pk=pk)
        data = dict(request.data)

        if "garment_type" in data and data["garment_type"] != existing.garment_type:
            raise ValidationError(
                {
                    "garment_type": (
                        "Cannot change the garment type of a measurement. "
                        "Create a new measurement for the other garment type."
                    )
                }
            )
        data["garment_type"] = existing.garment_type

        serializer = MeasurementSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            customer=existing.customer, garment_type=existing.garment_type
        )
        return Response(
            MeasurementSerializer(instance).data,
            status=http_status.HTTP_201_CREATED,
        )
