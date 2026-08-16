"""Invoice, customer payment and bill API views for Phase 9 + Phase 11.

Permission model (backend authoritative):
- Reads (list/detail, payment history, bill) -> OWNER or STAFF.
- Mutations (create invoice, record payment) -> STAFF only.

Invoices are never updated or deleted (no update/delete routes) and customer
payments are append-only. Payment recording runs through
``apps.billing.services.record_customer_payment``, which locks the invoice row
so concurrent requests cannot overpay; payment types (ADVANCE / PARTIAL /
FINAL / REFUND) are validated against the server-derived balance under that
lock. The ``bill`` endpoint assembles a digital bill entirely from database
data (``apps.billing.services.build_bill_data``). All list filtering honours
inclusive date boundaries and validates its inputs.
"""

from datetime import date

from django.db.models import Case, DecimalField, F, OuterRef, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.common.pagination import SaamuPageNumberPagination
from apps.orders.models import Order

from .communications import build_automatic_order_communication
from .models import CustomerPayment, Invoice, ManualReminder, ShopDetails
from .reminder_service import (
    REMINDER_CATEGORIES,
    REMINDER_MANUAL,
    REMINDER_TYPES,
    build_pending_reminder_candidates,
    reminder_summary,
)
from .reminders import (
    ReminderNotEligible,
    build_pending_reminders,
    build_reminder_candidate,
    parse_reminder_id,
)
from .serializers import (
    CustomerPaymentCreateSerializer,
    CustomerPaymentSerializer,
    InvoiceCreateSerializer,
    InvoiceEligibleOrderSerializer,
    InvoiceSerializer,
    ManualReminderCreateSerializer,
    ManualReminderSerializer,
    ShopDetailsSerializer,
)
from .services import build_bill_data, record_customer_payment


class ShopDetailsView(APIView):
    """Shop/business profile endpoint for the Settings module.

    ``GET /api/v1/settings/shop-details/`` returns the database-backed
    ``ShopDetails`` singleton (OWNER or STAFF) and ``PUT`` updates it (STAFF
    only), so shop identity is managed through one authoritative source and is
    never mocked on the client. OWNER remains view-only; STAFF manages the shop
    profile, matching the READ -> OWNER+STAFF / MUTATE -> STAFF permission
    model used across billing and payroll configuration.
    """

    http_method_names = ["get", "put", "head", "options"]

    def get_permissions(self):
        if self.request.method == "PUT":
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get(self, request):
        return Response(ShopDetailsSerializer(ShopDetails.shop_details()).data)

    def put(self, request):
        details = ShopDetails.shop_details()
        serializer = ShopDetailsSerializer(details, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


def _parse_date(value, field_name):
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise ValidationError({field_name: "Enter a valid date (YYYY-MM-DD)."})


def _parse_range(request):
    """Parse and validate the inclusive date_from/date_to query range."""
    date_from = _parse_date(request.query_params.get("date_from"), "date_from")
    date_to = _parse_date(request.query_params.get("date_to"), "date_to")
    if date_from and date_to and date_to < date_from:
        raise ValidationError({"date_to": "date_to cannot be earlier than date_from."})
    return date_from, date_to


class InvoiceViewSet(viewsets.ModelViewSet):
    """Invoices with OWNER+STAFF reads and STAFF creation only."""

    http_method_names = ["get", "post", "head", "options"]
    serializer_class = InvoiceSerializer
    pagination_class = SaamuPageNumberPagination

    def get_permissions(self):
        if self.action == "create":
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_serializer_class(self):
        if self.action == "create":
            return InvoiceCreateSerializer
        return InvoiceSerializer

    def get_queryset(self):
        qs = (
            Invoice.objects.select_related("order__customer", "created_by")
            .prefetch_related("items", "payments")
            .all()
        )
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        """Search + customer/order + derived status + inclusive date filters.

        ``search`` matches invoice number, order number, customer name or
        customer mobile. ``status`` is filtered by re-deriving it from the
        payment totals, so it can never rely on a stored value.
        """
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(invoice_number__icontains=search)
                | Q(order__order_number__icontains=search)
                | Q(order__customer__full_name__icontains=search)
                | Q(order__customer__mobile_number__icontains=search)
            )

        customer = (self.request.query_params.get("customer") or "").strip()
        if customer:
            qs = qs.filter(order__customer_id=customer)

        order = (self.request.query_params.get("order") or "").strip()
        if order:
            qs = qs.filter(order_id=order)

        status_filter = (self.request.query_params.get("status") or "").strip()
        if status_filter:
            if status_filter not in Invoice.Status.values:
                raise ValidationError({"status": "Invalid invoice status filter."})
            net_paid = (
                CustomerPayment.objects.filter(invoice=OuterRef("pk"))
                .values("invoice")
                .annotate(
                    net=Sum(
                        Case(
                            When(
                                payment_type=CustomerPayment.PaymentType.REFUND,
                                then=-F("amount"),
                            ),
                            default=F("amount"),
                            output_field=DecimalField(max_digits=12, decimal_places=2),
                        )
                    )
                )
                .values("net")
            )
            qs = qs.annotate(
                _amount_paid=Coalesce(
                    net_paid,
                    Value(
                        0, output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                )
            )
            if status_filter == Invoice.Status.UNPAID:
                qs = qs.filter(_amount_paid__lte=0)
            elif status_filter == Invoice.Status.PAID:
                qs = qs.filter(_amount_paid__gte=F("total_amount"))
            else:
                qs = qs.filter(_amount_paid__gt=0).filter(
                    _amount_paid__lt=F("total_amount")
                )

        date_from, date_to = _parse_range(self.request)
        if date_from:
            qs = qs.filter(invoice_date__gte=date_from)
        if date_to:
            qs = qs.filter(invoice_date__lte=date_to)

        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        return Response(
            InvoiceSerializer(invoice, context=self.get_serializer_context()).data,
            status=http_status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="available-orders")
    def available_orders(self, request):
        """Orders eligible for invoicing (no invoice yet), OWNER or STAFF.

        The Create Invoice flow only ever presents this list, so an
        already-invoiced order cannot be picked from the UI. The backend stays
        authoritative: ``invoice__isnull`` excludes every order that already
        has an invoice, and the same rule is enforced again on creation.
        ``search`` matches order number, customer name or customer mobile.
        """
        search = (request.query_params.get("search") or "").strip()
        qs = Order.objects.select_related("customer").filter(invoice__isnull=True)
        if search:
            qs = qs.filter(
                Q(order_number__icontains=search)
                | Q(customer__full_name__icontains=search)
                | Q(customer__mobile_number__icontains=search)
            )
        # This action backs the Create Invoice order picker, not a list page, so
        # it keeps the global page size instead of the 6-per-page list standard.
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = InvoiceEligibleOrderSerializer(
            page, many=True, context=self.get_serializer_context()
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="payments")
    def payments(self, request, pk=None):
        """Payment history (GET) or record a payment (POST, STAFF)."""
        invoice = self.get_object()

        if request.method == "GET":
            qs = (
                CustomerPayment.objects.filter(invoice=invoice)
                .select_related("invoice", "recorded_by")
                .all()
            )
            qs = self._apply_payment_filters(qs)
            # Payment history is a sub-resource, not a list page, so it keeps
            # the global page size instead of the 6-per-page list standard.
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(qs, request, view=self)
            serializer = CustomerPaymentSerializer(
                page, many=True, context=self.get_serializer_context()
            )
            return paginator.get_paginated_response(serializer.data)

        if not IsStaffRole().has_permission(request, self):
            raise PermissionDenied("Only staff can record customer payments.")

        serializer = CustomerPaymentCreateSerializer(
            data=request.data,
            context={"invoice": invoice, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment = record_customer_payment(
            invoice=invoice,
            amount=data["amount"],
            payment_date=data.get("payment_date"),
            payment_method=data["payment_method"],
            payment_type=data.get("payment_type"),
            refunded_payment=data.get("refunded_payment"),
            reference=data.get("reference", ""),
            notes=data.get("notes", ""),
            recorded_by=request.user,
        )
        # Re-fetch the invoice so the response reflects the newly recorded
        # payment (the pre-fetched payment set on `invoice` is stale).
        invoice = self.get_object()
        return Response(
            {
                "success": True,
                "message": "Payment recorded successfully.",
                "payment": CustomerPaymentSerializer(
                    payment, context=self.get_serializer_context()
                ).data,
                "invoice": InvoiceSerializer(
                    invoice, context=self.get_serializer_context()
                ).data,
            },
            status=http_status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="bill")
    def bill(self, request, pk=None):
        """Digital bill for printing/sharing (OWNER or STAFF).

        Every value is assembled server-side from the database - shop profile,
        customer, order, garment snapshots, payment history and totals - so the
        rendered bill can never show mock or stale data.
        """
        invoice = self.get_object()
        return Response({"success": True, "bill": build_bill_data(invoice)})

    def _apply_payment_filters(self, qs):
        date_from, date_to = _parse_range(self.request)
        if date_from:
            qs = qs.filter(payment_date__gte=date_from)
        if date_to:
            qs = qs.filter(payment_date__lte=date_to)

        method = (self.request.query_params.get("payment_method") or "").strip()
        if method:
            if method not in CustomerPayment.Method.values:
                raise ValidationError(
                    {"payment_method": "Invalid payment method filter."}
                )
            qs = qs.filter(payment_method=method)
        return qs


class CommunicationMessagePrepareView(APIView):
    """Prepare the automatically selected WhatsApp-ready message (GET, read-only).

    ``GET /api/v1/communications/messages/prepare/order/<order_id>/`` returns the
    server-authored plain-text message together with a normalized destination
    and WhatsApp handoff URL. The message type is derived automatically from the
    current order status + authoritative payment balance — staff never choose a
    message type. The payload only ever reflects backend-authoritative data;
    nothing is sent, stored or logged. The user decides whether to copy the
    message or open WhatsApp in the browser.

    A ready-for-collection message is only ever produced for an order that is
    actually READY, and collected messages distinguish fully-settled orders from
    those with an outstanding balance, so the message never makes an
    unsupported claim. CANCELLED orders have no communication message.
    """

    http_method_names = ["get"]
    permission_classes = [IsOwnerOrStaff]

    def get(self, request, order_id):
        order = get_object_or_404(Order.objects.select_related("customer"), pk=order_id)
        try:
            data = build_automatic_order_communication(order)
        except ValueError as exc:
            raise ValidationError({"message": f"{exc}"})
        return Response({"success": True, "data": data})


class ReminderListAPIView(APIView):
    """List the currently eligible reminder candidates (GET, read-only).

    ``GET /api/v1/communications/reminders/`` derives the pending reminders
    from authoritative order and payment state and prepares each message via
    the Phase 18 communication layer. Reminders are never stored, so repeated
    requests on unchanged state return the identical deterministic set.
    """

    http_method_names = ["get"]
    permission_classes = [IsOwnerOrStaff]
    pagination_class = SaamuPageNumberPagination

    def get(self, request):
        candidates = build_pending_reminders()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(candidates, request, view=self)
        return Response(
            {
                "success": True,
                "data": {
                    "count": paginator.page.paginator.count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": page,
                },
            }
        )


class ReminderPrepareAPIView(APIView):
    """Prepare one reminder for review/action (GET, read-only).

    ``GET /api/v1/communications/reminders/<reminder_id>/prepare/`` where
    ``reminder_id`` is the stable derived id ``<TYPE>_<order_id>`` (e.g.
    ``READY_FOR_COLLECTION_12``). Current eligibility is re-evaluated before
    the message is prepared, so a stale reminder (the order changed state since
    it was listed) yields a clear 400 ``validation_error`` instead of being
    forced through inconsistent business state.
    """

    http_method_names = ["get"]
    permission_classes = [IsOwnerOrStaff]

    def get(self, request, reminder_id):
        parsed = parse_reminder_id(reminder_id)
        if parsed is None:
            raise ValidationError({"reminder_id": "Invalid reminder id."})
        reminder_type, order_id = parsed
        order = get_object_or_404(Order.objects.select_related("customer"), pk=order_id)
        try:
            candidate = build_reminder_candidate(order, reminder_type)
        except ReminderNotEligible as exc:
            raise ValidationError({"reminder_id": f"{exc.message} ({exc.code})."})
        return Response({"success": True, "data": candidate})


class ReminderV1ListView(APIView):
    """List the currently eligible Reminders V1 candidates (GET, read-only).

    ``GET /api/v1/reminders/`` derives automatic reminders from authoritative
    order, payment, measurement, tailor and customer state and merges in the
    persisted PENDING manual reminders. Filters (all optional): ``type``
    (one of ``REMINDER_TYPES``), ``category`` (orders/payments/tailors/
    customers/manual), ``priority`` (manual reminders only), ``date``
    (YYYY-MM-DD, matches a candidate's primary date) and ``search`` (matches
    order number, customer name, tailor name, title/description). Results are
    paginated and deterministically ordered.
    """

    http_method_names = ["get"]
    permission_classes = [IsOwnerOrStaff]
    pagination_class = SaamuPageNumberPagination

    def get(self, request):
        candidates = build_pending_reminder_candidates()
        candidates = self._apply_filters(candidates, request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(candidates, request, view=self)
        return Response(
            {
                "success": True,
                "data": {
                    "count": paginator.page.paginator.count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": page,
                },
            }
        )

    def _apply_filters(self, candidates, request):
        reminder_type = (request.query_params.get("type") or "").strip()
        if reminder_type:
            if reminder_type not in REMINDER_TYPES:
                raise ValidationError({"type": "Invalid reminder type filter."})
            candidates = [c for c in candidates if c["reminder_type"] == reminder_type]

        category = (request.query_params.get("category") or "").strip()
        if category:
            if category not in REMINDER_CATEGORIES.values():
                raise ValidationError({"category": "Invalid reminder category filter."})
            candidates = [c for c in candidates if c["category"] == category]

        priority = (request.query_params.get("priority") or "").strip()
        if priority:
            if priority not in ManualReminder.Priority.values:
                raise ValidationError({"priority": "Invalid priority filter."})
            candidates = [c for c in candidates if c["priority"] == priority]

        date_value = _parse_date(request.query_params.get("date"), "date")
        if date_value:
            candidates = [c for c in candidates if c["date"] == date_value]

        search = (request.query_params.get("search") or "").strip().lower()
        if search:
            matched = []
            for c in candidates:
                haystack = " ".join(
                    part
                    for part in (
                        c["title"],
                        c["description"],
                        (c["order"] or {}).get("order_number"),
                        (c["customer"] or {}).get("full_name"),
                        (c["tailor"] or {}).get("full_name"),
                    )
                    if part
                ).lower()
                if search in haystack:
                    matched.append(c)
            candidates = matched
        return candidates


class ReminderSummaryView(APIView):
    """Counts of currently eligible reminders per type and category (GET).

    ``GET /api/v1/reminders/summary/`` returns the unfiltered totals so the
    Reminders page can render its summary cards without pagination affecting
    the counts.
    """

    http_method_names = ["get"]
    permission_classes = [IsOwnerOrStaff]

    def get(self, request):
        return Response({"success": True, "data": reminder_summary()})


class ManualReminderViewSet(viewsets.ModelViewSet):
    """Manual reminders: OWNER/STAFF reads, STAFF-only mutations.

    Manual reminders are the only persisted reminders. ``complete`` and
    ``cancel`` transition a PENDING reminder so it leaves the pending queue
    without ever being physically deleted (rows remain as an audit trail).
    """

    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = ManualReminderSerializer
    pagination_class = SaamuPageNumberPagination
    MANUAL_MUTATION_ACTIONS = {"create", "partial_update", "complete", "cancel"}

    def get_permissions(self):
        if self.action in self.MANUAL_MUTATION_ACTIONS:
            return [IsStaffRole()]
        return [IsOwnerOrStaff()]

    def get_serializer_class(self):
        if self.action in {"create", "partial_update"}:
            return ManualReminderCreateSerializer
        return ManualReminderSerializer

    def get_queryset(self):
        qs = ManualReminder.objects.select_related("customer", "order").all()
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs

    def _apply_list_filters(self, qs):
        status = (self.request.query_params.get("status") or "").strip()
        if status:
            if status not in ManualReminder.Status.values:
                raise ValidationError({"status": "Invalid manual reminder status."})
            qs = qs.filter(status=status)

        priority = (self.request.query_params.get("priority") or "").strip()
        if priority:
            if priority not in ManualReminder.Priority.values:
                raise ValidationError({"priority": "Invalid priority filter."})
            qs = qs.filter(priority=priority)

        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(customer__full_name__icontains=search)
                | Q(order__order_number__icontains=search)
            )
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        reminder = serializer.save()
        return Response(
            ManualReminderSerializer(
                reminder, context=self.get_serializer_context()
            ).data,
            status=http_status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        reminder = self.get_object()
        if reminder.status != ManualReminder.Status.PENDING:
            raise ValidationError(
                {"status": "Only PENDING reminders can be completed."}
            )
        reminder.status = ManualReminder.Status.COMPLETED
        reminder.completed_at = timezone.now()
        reminder.completed_by = request.user
        reminder.save(
            update_fields=["status", "completed_at", "completed_by", "updated_at"]
        )
        return Response(
            {
                "success": True,
                "message": "Reminder marked as completed.",
                "reminder": ManualReminderSerializer(
                    reminder, context=self.get_serializer_context()
                ).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        reminder = self.get_object()
        if reminder.status != ManualReminder.Status.PENDING:
            raise ValidationError(
                {"status": "Only PENDING reminders can be cancelled."}
            )
        reminder.status = ManualReminder.Status.CANCELLED
        reminder.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "success": True,
                "message": "Reminder cancelled.",
                "reminder": ManualReminderSerializer(
                    reminder, context=self.get_serializer_context()
                ).data,
            }
        )
