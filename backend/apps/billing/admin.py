from django.contrib import admin

from .models import (
    CustomerPayment,
    Invoice,
    InvoiceItem,
    ManualReminder,
    ShopDetails,
)


@admin.register(ShopDetails)
class ShopDetailsAdmin(admin.ModelAdmin):
    list_display = ("name", "tagline", "phone", "established_year", "updated_at")
    readonly_fields = ("id", "created_at", "updated_at")

    def has_add_permission(self, request):
        # Enforce the singleton from the admin: creation happens via
        # ``ShopDetails.shop_details()`` on first access.
        return not ShopDetails.objects.exists()


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "invoice_number",
        "order",
        "invoice_date",
        "subtotal",
        "total_amount",
        "created_by",
        "created_at",
    )
    list_filter = ("invoice_date",)
    ordering = ("-invoice_date",)
    readonly_fields = ("created_by", "created_at", "updated_at")


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "invoice",
        "garment_type",
        "garment_code",
        "quantity",
        "unit_price",
        "line_total",
    )
    ordering = ("invoice", "id")


@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "invoice",
        "payment_type",
        "amount",
        "payment_date",
        "payment_method",
        "reference",
        "recorded_by",
        "created_at",
    )
    list_filter = ("payment_type", "payment_method", "payment_date")
    ordering = ("-payment_date",)
    readonly_fields = ("recorded_by", "created_at", "updated_at")


@admin.register(ManualReminder)
class ManualReminderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "reminder_date",
        "priority",
        "status",
        "customer",
        "order",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "priority", "reminder_date")
    ordering = ("-reminder_date",)
    readonly_fields = (
        "created_by",
        "completed_by",
        "completed_at",
        "created_at",
        "updated_at",
    )
