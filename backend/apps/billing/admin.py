from django.contrib import admin

from .models import CustomerPayment, Invoice, InvoiceItem


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
        "amount",
        "payment_date",
        "payment_method",
        "reference",
        "recorded_by",
        "created_at",
    )
    list_filter = ("payment_method", "payment_date")
    ordering = ("-payment_date",)
    readonly_fields = ("recorded_by", "created_at", "updated_at")
