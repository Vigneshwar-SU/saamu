from django.contrib import admin

from .models import Customer, Measurement

ALL_MEASUREMENT_FIELDS = (
    "neck_circumference",
    "chest_circumference",
    "waist_circumference",
    "hip_circumference",
    "shoulder_width",
    "sleeve_length",
    "sleeve_circumference",
    "cuff_circumference",
    "shirt_length",
    "thigh_circumference",
    "knee_circumference",
    "bottom_circumference",
    "length",
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "mobile_number", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("full_name", "mobile_number", "alternate_mobile_number")
    ordering = ("-id",)


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "garment_type",
        "version",
        "is_current",
        "updated_at",
    )
    list_filter = ("garment_type", "is_current")
    search_fields = ("customer__full_name", "customer__mobile_number")
    readonly_fields = (
        "id",
        "customer",
        "version",
        "is_current",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Measurement",
            {"fields": ("customer", "garment_type", "version", "is_current", "notes")},
        ),
        ("Values (inches)", {"fields": ALL_MEASUREMENT_FIELDS}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
