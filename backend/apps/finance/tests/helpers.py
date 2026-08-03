"""Shared helpers for income, expense and dashboard tests."""

from datetime import date

from apps.customers.tests.helpers import make_owner, make_staff  # noqa: F401
from apps.finance.models import Expense, Income


def income_list_url():
    return "/api/v1/income/"


def income_detail_url(income_id):
    return f"/api/v1/income/{income_id}/"


def expenses_list_url():
    return "/api/v1/expenses/"


def expense_detail_url(expense_id):
    return f"/api/v1/expenses/{expense_id}/"


def dashboard_summary_url():
    return "/api/v1/dashboard/summary/"


def create_income(amount="500.00", income_date=None, **kwargs):
    defaults = {
        "category": Income.Category.ORDER_PAYMENT,
        "amount": amount,
        "income_date": income_date or date.today(),
    }
    defaults.update(kwargs)
    return Income.objects.create(**defaults)


def create_expense(amount="100.00", expense_date=None, **kwargs):
    defaults = {
        "category": Expense.Category.MATERIAL,
        "amount": amount,
        "expense_date": expense_date or date.today(),
    }
    defaults.update(kwargs)
    return Expense.objects.create(**defaults)
