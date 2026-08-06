"""Reports CSV/PDF export API tests (Phase 17).

Exports are a thin presentation layer over the authoritative
``build_reports_summary`` aggregation (the same source of truth used by the
reports page), so exported values must always agree with the reports summary.
These tests assert RBAC, date-range semantics (inclusive boundaries, invalid
and reversed ranges), CSV structure and stable headers, exact money rendering,
PDF validity and content, safe file names, no secret leakage, and that exports
never mutate business records.
"""

import csv
import io
from datetime import date, timedelta

import pytest

from apps.authentication.tests.helpers import auth_header
from apps.billing.models import CustomerPayment
from apps.billing.tests.helpers import create_invoice
from apps.billing.tests.helpers import create_payment as create_customer_payment
from apps.customers.models import Customer
from apps.customers.tests.helpers import create_customer
from apps.finance.models import Expense
from apps.finance.report_exports import _money
from apps.finance.services import build_reports_summary
from apps.finance.tests.helpers import (
    create_expense,
    make_owner,
    make_staff,
    reports_export_csv_url,
    reports_export_pdf_url,
)
from apps.orders.models import Order
from apps.payments.tests.helpers import (
    create_advance,
    create_finalized_entry,
    create_payment,
)
from apps.tailors.models import WorkAssignment
from apps.tailors.tests.helpers import (
    create_assignment,
    create_order_with_items,
    create_piece_rate,
    create_tailor,
    get_order_item,
)

pytestmark = pytest.mark.django_db

TODAY = date.today()


@pytest.fixture
def staff():
    return make_staff()


@pytest.fixture
def owner():
    return make_owner()


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _csv(client, user, **params):
    return client.get(reports_export_csv_url(), params, **_auth(user))


def _pdf(client, user, **params):
    return client.get(reports_export_pdf_url(), params, **_auth(user))


def _csv_rows(content):
    return list(csv.reader(io.StringIO(content.decode("utf-8"))))


def _csv_metrics(content, section):
    """Map of metric label -> value for a two-column section in the CSV."""
    rows = _csv_rows(content)
    metrics = {}
    current = None
    for row in rows:
        if len(row) == 1 and row[0] and not row[0].startswith("Saamu"):
            current = row[0]
            continue
        if current == section and len(row) == 2 and row != ["Metric", "Value"]:
            metrics[row[0]] = row[1]
    return metrics


def _payment(invoice=None, amount="500.00", payment_date=None, **extra):
    return create_customer_payment(
        invoice or create_invoice(),
        amount=amount,
        payment_date=payment_date or TODAY,
        **extra,
    )


def _seed_full_dataset():
    """Order + payments + expenses + workload that give exact, known totals."""
    customer = create_customer("Report Customer", "9123456780")
    tailor = create_tailor()
    create_piece_rate(garment_type="SHIRT", rate_per_piece="150.00")

    order = create_order_with_items(customer, {"SHIRT": 3, "PANT": 2})
    invoice = create_invoice(order)
    create_customer_payment(
        invoice,
        amount="500.00",
        payment_date=TODAY,
        payment_type=CustomerPayment.PaymentType.FINAL,
        method=CustomerPayment.Method.CASH,
    )
    create_customer_payment(
        invoice,
        amount="100.00",
        payment_date=TODAY,
        payment_type=CustomerPayment.PaymentType.REFUND,
        method=CustomerPayment.Method.CASH,
    )
    create_expense(
        amount="120.50",
        expense_date=TODAY,
        category=Expense.Category.MATERIAL,
    )
    create_expense(
        amount="30.00",
        expense_date=TODAY,
        category=Expense.Category.RENT,
    )
    create_assignment(
        tailor,
        get_order_item(order, "SHIRT"),
        assigned_quantity=3,
        completed_quantity=2,
        status=WorkAssignment.Status.IN_PROGRESS,
        rate_per_piece_snapshot="150.00",
    )
    return customer, order


def test_anonymous_denied(client):
    assert client.get(reports_export_csv_url()).status_code == 401
    assert client.get(reports_export_pdf_url()).status_code == 401


def test_owner_and_staff_can_export_both_formats(client, owner, staff):
    for user in (owner, staff):
        csv_response = _csv(client, user)
        assert csv_response.status_code == 200
        assert csv_response["Content-Type"] == "text/csv; charset=utf-8"

        pdf_response = _pdf(client, user)
        assert pdf_response.status_code == 200
        assert pdf_response["Content-Type"] == "application/pdf"


def test_mutation_methods_rejected(client, staff):
    for url in (reports_export_csv_url(), reports_export_pdf_url()):
        assert client.post(url, {}, **_auth(staff)).status_code == 405
        assert client.put(url, {}, **_auth(staff)).status_code == 405
        assert client.patch(url, {}, **_auth(staff)).status_code == 405
        assert client.delete(url, **_auth(staff)).status_code == 405


def test_csv_structure_and_stable_headers(client, staff):
    response = _csv(client, staff)
    rows = _csv_rows(response.content)

    assert rows[0] == ["Saamu Tailors - Business Report"]
    assert [row[1] for row in rows if row and row[0] == "Report period"] == [
        "Beginning to Today"
    ]

    section_titles = [row[0] for row in rows if len(row) == 1 and row[0]]
    for title in (
        "Orders",
        "Garment Quantities",
        "Customers",
        "Tailor Workload",
        "Financial Summary",
        "Income by Payment Method",
        "Income by Payment Type",
        "Expenses by Category",
        "Expenses by Payment Method",
    ):
        assert title in section_titles

    headers = [tuple(row) for row in rows]
    for header in (
        ("Order Status", "Count"),
        ("Garment Type", "Quantity"),
        ("Metric", "Value"),
        ("Payment Method", "Total", "Count"),
        ("Payment Type", "Total", "Count"),
        ("Category", "Total", "Count"),
    ):
        assert header in headers


def test_csv_values_match_authoritative_aggregation(client, staff):
    _seed_full_dataset()

    summary = build_reports_summary()
    response = _csv(client, staff)
    metrics = _csv_metrics(response.content, "Financial Summary")

    assert metrics["Income (total)"] == _money(
        summary["financial"]["income"]["total_income"]
    )
    assert metrics["Income payment count"] == str(
        summary["financial"]["income"]["payment_count"]
    )
    assert metrics["Refund count"] == str(
        summary["financial"]["income"]["refund_count"]
    )
    assert metrics["Total refunds"] == _money(
        summary["financial"]["income"]["total_refunds"]
    )
    assert metrics["Expenses (total)"] == _money(
        summary["financial"]["expenses"]["total_expenses"]
    )
    assert metrics["Expense count"] == str(
        summary["financial"]["expenses"]["expense_count"]
    )
    assert metrics["Net position"] == _money(summary["financial"]["net_position"])
    assert metrics["Payroll paid in range"] == _money(
        summary["financial"]["payroll_paid"]
    )
    assert metrics["Salary advances in range"] == _money(
        summary["financial"]["salary_advances"]
    )
    assert metrics["Order revenue"] == _money(summary["financial"]["order_revenue"])


def test_csv_renders_exact_money_and_counts(client, staff):
    _seed_full_dataset()

    rows = _csv_rows(_csv(client, staff).content)

    assert ["Income (total)", "400.00"] in rows
    assert ["Income payment count", "1"] in rows
    assert ["Refund count", "1"] in rows
    assert ["Total refunds", "100.00"] in rows
    assert ["Expenses (total)", "150.50"] in rows
    assert ["Expense count", "2"] in rows
    assert ["Net position", "249.50"] in rows
    assert ["Order revenue", "500.00"] in rows

    assert ["SHIRT", "3"] in rows
    assert ["PANT", "2"] in rows
    assert ["New", "1"] in rows


def test_csv_includes_payroll_and_advances(client, staff):
    entry = create_finalized_entry()
    create_payment(entry, amount="750.00", payment_date=TODAY)
    create_advance(create_tailor(), amount="200.00", advance_date=TODAY)

    rows = _csv_rows(_csv(client, staff).content)
    assert ["Payroll paid in range", "750.00"] in rows
    assert ["Salary advances in range", "200.00"] in rows

    metrics = _csv_metrics(_csv(client, staff).content, "Financial Summary")
    assert metrics["Payroll paid in range"] == "750.00"
    assert metrics["Salary advances in range"] == "200.00"


def test_csv_honors_inclusive_date_range(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00", payment_date=TODAY)
    _payment(invoice=invoice, amount="200.00", payment_date=TODAY + timedelta(days=3))
    _payment(invoice=invoice, amount="300.00", payment_date=TODAY - timedelta(days=3))

    response = _csv(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY + timedelta(days=3)),
    )
    metrics = _csv_metrics(response.content, "Financial Summary")
    assert metrics["Income (total)"] == "300.00"
    assert metrics["Income payment count"] == "2"

    period = [
        row for row in _csv_rows(response.content) if row and row[0] == "Report period"
    ]
    assert period == [
        [
            "Report period",
            f"{TODAY} to {TODAY + timedelta(days=3)}",
        ]
    ]


def test_csv_uses_applied_range_only(client, staff):
    _payment(amount="100.00", payment_date=TODAY)
    _payment(amount="200.00", payment_date=TODAY - timedelta(days=5))
    _payment(amount="300.00", payment_date=TODAY + timedelta(days=5))

    all_time = _csv(client, staff).content
    assert _csv_metrics(all_time, "Financial Summary")["Income (total)"] == "600.00"

    from_only = _csv(client, staff, date_from=str(TODAY)).content
    assert _csv_metrics(from_only, "Financial Summary")["Income (total)"] == "400.00"

    to_only = _csv(client, staff, date_to=str(TODAY)).content
    assert _csv_metrics(to_only, "Financial Summary")["Income (total)"] == "300.00"


def test_invalid_and_reversed_dates_return_400(client, staff):
    for url in (reports_export_csv_url(), reports_export_pdf_url()):
        invalid = client.get(url, {"date_from": "not-a-date"}, **_auth(staff))
        assert invalid.status_code == 400
        assert invalid.json()["success"] is False
        assert invalid.json()["error"]["code"] == "validation_error"

        reversed_range = client.get(
            url,
            {"date_from": str(TODAY), "date_to": str(TODAY - timedelta(days=1))},
            **_auth(staff),
        )
        assert reversed_range.status_code == 400


def test_safe_filename_in_content_disposition(client, staff):
    csv_response = _csv(client, staff)
    pdf_response = _pdf(client, staff)
    assert (
        csv_response["Content-Disposition"]
        == 'attachment; filename="saamu-tailors-report-all-time.csv"'
    )
    assert (
        pdf_response["Content-Disposition"]
        == 'attachment; filename="saamu-tailors-report-all-time.pdf"'
    )


def test_filename_derives_from_range(client, staff):
    from_response = _csv(client, staff, date_from=str(TODAY))
    assert (
        f'filename="saamu-tailors-report-from_{TODAY}.csv"'
        in from_response["Content-Disposition"]
    )

    to_response = _csv(client, staff, date_to=str(TODAY))
    assert (
        f'filename="saamu-tailors-report-to_{TODAY}.csv"'
        in to_response["Content-Disposition"]
    )

    both_response = _csv(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY + timedelta(days=1)),
    )
    assert (
        f'filename="saamu-tailors-report-{TODAY}_to_{TODAY + timedelta(days=1)}.csv"'
        in both_response["Content-Disposition"]
    )


def test_pdf_is_valid_and_non_empty(client, staff):
    response = _pdf(client, staff)
    content = response.content
    assert content.startswith(b"%PDF-1.")
    assert content.rstrip().endswith(b"%%EOF")
    assert len(content) > 1000


def test_pdf_contains_expected_sections_and_amounts(client, staff):
    _seed_full_dataset()

    content = _pdf(client, staff).content

    for section in (
        b"Saamu Tailors - Business Report",
        b"Financial Summary",
        b"Orders",
        b"Customers",
        b"Tailor Workload",
        b"Payroll & Settlements",
        b"Income by Payment Type",
        b"Expenses by Category",
    ):
        assert section in content

    for amount in (b"Rs 400.00", b"Rs 150.50", b"Rs 249.50", b"Rs 500.00"):
        assert amount in content


def test_pdf_honors_inclusive_date_range(client, staff):
    invoice = create_invoice()
    _payment(invoice=invoice, amount="100.00", payment_date=TODAY)
    _payment(invoice=invoice, amount="200.00", payment_date=TODAY + timedelta(days=3))

    content = _pdf(
        client,
        staff,
        date_from=str(TODAY),
        date_to=str(TODAY + timedelta(days=3)),
    ).content
    assert b"Rs 300.00" in content


def test_export_contains_no_secrets_or_contact_data(client, staff):
    create_customer("Leak Test Customer", "9876543210", notes="SECRET-NOTES-42")
    _payment(amount="500.00")

    csv_content = _csv(client, staff).content
    pdf_content = _pdf(client, staff).content

    for secret in (b"SECRET-NOTES-42", b"9876543210", b"Leak Test Customer"):
        assert secret not in csv_content
        assert secret not in pdf_content


def test_export_never_mutates_records(client, staff):
    customer = create_customer()
    create_order_with_items(customer, {"SHIRT": 1})
    _payment(amount="100.00")
    create_expense(amount="50.00", expense_date=TODAY)

    before = {
        "customers": Customer.objects.count(),
        "orders": Order.objects.count(),
        "expenses": Expense.objects.count(),
        "payments": CustomerPayment.objects.count(),
    }

    _csv(client, staff)
    _pdf(client, staff)

    after = {
        "customers": Customer.objects.count(),
        "orders": Order.objects.count(),
        "expenses": Expense.objects.count(),
        "payments": CustomerPayment.objects.count(),
    }
    assert after == before
