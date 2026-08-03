from django.contrib import admin

from .models import Expense, Income


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "category",
        "amount",
        "income_date",
        "reference",
        "recorded_by",
        "created_at",
    )
    list_filter = ("category",)
    ordering = ("-income_date",)
    readonly_fields = ("recorded_by", "created_at", "updated_at")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "category",
        "amount",
        "expense_date",
        "reference",
        "recorded_by",
        "created_at",
    )
    list_filter = ("category",)
    ordering = ("-expense_date",)
    readonly_fields = ("recorded_by", "created_at", "updated_at")
