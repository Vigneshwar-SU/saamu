from django.contrib import admin

from .models import PayrollPayment, SalaryAdvance


@admin.register(SalaryAdvance)
class SalaryAdvanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tailor",
        "amount",
        "advance_date",
        "status",
        "recorded_by",
        "created_at",
    )
    list_filter = ("status",)
    ordering = ("-advance_date",)


@admin.register(PayrollPayment)
class PayrollPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payroll_entry",
        "tailor",
        "amount",
        "payment_date",
        "payment_method",
        "reference",
        "recorded_by",
        "created_at",
    )
    list_filter = ("payment_method",)
    ordering = ("-payment_date",)
