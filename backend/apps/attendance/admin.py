from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tailor",
        "attendance_date",
        "status",
        "marked_by",
        "created_at",
    )
    list_filter = ("status", "attendance_date", "tailor")
    search_fields = ("tailor__full_name",)
    ordering = ("-attendance_date",)
    readonly_fields = ("marked_by",)
