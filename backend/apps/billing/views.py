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
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsOwnerOrStaff, IsStaffRole
from apps.orders.models import Order, OrderStatus

from .communications import (
    MESSAGE_TYPE_READY_FOR_COLLECTION,
    SUPPORTED_MESSAGE_TYPES,
    build_order_communication,
)
from .models import CustomerPayment, Invoice
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
    InvoiceSerializer,
)
from .services import build_bill_data, record_customer_payment


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
            page = self.paginate_queryset(qs)
            serializer = CustomerPaymentSerializer(
                page, many=True, context=self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)

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
    """Prepare a WhatsApp-ready customer message (GET, read-only).

    ``GET /api/v1/communications/messages/prepare/order/<order_id>/?message_type=...``
    returns the server-authored plain-text message together with a normalized
    destination and WhatsApp handoff URL. The payload only ever reflects
    backend-authoritative data; nothing is sent, stored or logged. The user
    decides whether to copy the message or open WhatsApp in the browser.

    Only the four supported message types are accepted. A ready-for-collection
    message can only be prepared when the order is actually READY, so the
    message never makes an unsupported claim.
    """

    http_method_names = ["get"]
    permission_classes = [IsOwnerOrStaff]

    def get(self, request, order_id):
        message_type = (request.query_params.get("message_type") or "").strip()
        if message_type not in SUPPORTED_MESSAGE_TYPES:
            raise ValidationError({"message_type": "Unsupported message type."})

        order = get_object_or_404(Order.objects.select_related("customer"), pk=order_id)
        if (
            message_type == MESSAGE_TYPE_READY_FOR_COLLECTION
            and order.status != OrderStatus.READY
        ):
            raise ValidationError(
                {
                    "message_type": (
                        "A ready-for-collection message can only be prepared for "
                        "an order that is ready. Current status: "
                        f"{order.get_status_display()}."
                    )
                }
            )

        data = build_order_communication(order, message_type)
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
    pagination_class = PageNumberPagination

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
