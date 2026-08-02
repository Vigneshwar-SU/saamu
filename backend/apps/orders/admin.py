from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_number",
        "customer",
        "status",
        "order_date",
        "expected_delivery_date",
        "total_amount",
        "collected_at",
    )
    list_filter = ("status", "order_date")
    search_fields = ("order_number", "customer__full_name", "customer__mobile_number")
    ordering = ("-id",)
    readonly_fields = (
        "order_number",
        "customer",
        "total_amount",
        "collected_at",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Order",
            {
                "fields": (
                    "order_number",
                    "customer",
                    "order_date",
                    "expected_delivery_date",
                    "status",
                    "notes",
                )
            },
        ),
        ("Totals", {"fields": ("total_amount",)}),
        ("Timestamps", {"fields": ("collected_at", "created_at", "updated_at")}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "garment_type",
        "quantity",
        "unit_price",
        "measurement_version",
    )
    list_filter = ("garment_type",)
    search_fields = ("order__order_number", "order__customer__full_name")
    readonly_fields = (
        "order",
        "measurement",
        "measurement_version",
        "measurement_snapshot",
        "created_at",
        "updated_at",
    )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "from_status",
        "to_status",
        "changed_by",
        "changed_at",
    )
    list_filter = ("to_status",)
    search_fields = ("order__order_number",)
    readonly_fields = (
        "order",
        "from_status",
        "to_status",
        "changed_by",
        "changed_at",
    )
