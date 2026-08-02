from django.contrib import admin

from .models import PieceRate, Tailor, WorkAssignment


@admin.register(Tailor)
class TailorAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "mobile_number", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("full_name", "mobile_number")
    ordering = ("-created_at",)


@admin.register(PieceRate)
class PieceRateAdmin(admin.ModelAdmin):
    list_display = ("id", "garment_type", "rate_per_piece", "is_active")
    list_filter = ("is_active", "garment_type")
    search_fields = ("garment_type",)
    ordering = ("garment_type",)


@admin.register(WorkAssignment)
class WorkAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tailor",
        "order_item",
        "assigned_quantity",
        "completed_quantity",
        "status",
        "rate_per_piece_snapshot",
        "assigned_at",
    )
    list_filter = ("status", "tailor")
    search_fields = ("tailor__full_name", "order_item__order__order_number")
    ordering = ("-assigned_at",)
    readonly_fields = ("assigned_at", "started_at", "completed_at", "created_by")
