from django.contrib import admin

from .models import PayrollEntry, PayrollPeriod


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "period_start",
        "period_end",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status",)
    ordering = ("-period_start",)
    readonly_fields = ("created_by",)


@admin.register(PayrollEntry)
class PayrollEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payroll_period",
        "tailor",
        "present_days",
        "half_days",
        "absent_days",
        "completed_pieces",
        "piece_rate_earnings",
        "total_payable",
    )
    list_filter = ("payroll_period", "tailor")
    ordering = ("payroll_period", "tailor")
