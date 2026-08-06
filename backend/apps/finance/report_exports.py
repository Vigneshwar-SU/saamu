"""CSV and PDF export of the reports & business-insights summary.

Phase 17 exports are a thin presentation layer over the authoritative
``build_reports_summary`` aggregation (the same single source of truth used by
``ReportsSummaryView``), so an exported file can never disagree with the
reports page and can never become a second source of truth. Both builders are
pure functions of the summary dict and always return bytes; no database
records are read here and no record is ever written or mutated.

Money values are rendered as two-decimal strings from ``Decimal`` so exported
totals are exact (never floating-point artifacts) and deterministic.
"""

import csv
import io
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from apps.orders.models import OrderStatus

_ONE_CENT = Decimal("0.01")

ORDER_STATUS_ORDER = [
    OrderStatus.NEW,
    OrderStatus.CUTTING,
    OrderStatus.STITCHING,
    OrderStatus.READY,
    OrderStatus.COLLECTED,
    OrderStatus.CANCELLED,
]

_CUSTOMER_METRICS = (
    ("Active customers", "customers.active_customers"),
    ("New customers in range", "customers.new_customers"),
    ("Customers with orders in range", "customers.customers_with_orders"),
)

_WORKLOAD_METRICS = (
    ("Active tailors", "tailors.active_tailors", False),
    ("Assigned pieces", "tailors.workload.assigned_quantity", False),
    ("Completed pieces", "tailors.workload.completed_quantity", False),
    ("Outstanding pieces", "tailors.workload.outstanding_quantity", False),
    ("Earnings earned", "tailors.workload.earned_amount", True),
)

_FINANCIAL_METRICS = (
    ("Net position", "financial.net_position", True),
    ("Income (total)", "financial.income.total_income", True),
    ("Income payment count", "financial.income.payment_count", False),
    ("Refund count", "financial.income.refund_count", False),
    ("Total refunds", "financial.income.total_refunds", True),
    ("Expenses (total)", "financial.expenses.total_expenses", True),
    ("Expense count", "financial.expenses.expense_count", False),
    ("Payroll paid in range", "financial.payroll_paid", True),
    ("Salary advances in range", "financial.salary_advances", True),
    ("Order revenue", "financial.order_revenue", True),
)


def _money(value):
    """Render a money value as an exact two-decimal string."""
    return f"{Decimal(str(value)).quantize(_ONE_CENT, rounding=ROUND_HALF_UP):.2f}"


def _format_range(range_info):
    date_from = range_info.get("date_from")
    date_to = range_info.get("date_to")
    return f"{date_from or 'Beginning'} to {date_to or 'Today'}"


def _rows_for_breakdown(rows, name_key):
    """Normalise a summary breakdown into (label, total, count) tuples.

    The aggregation services already return breakdowns ordered by their
    choices, so iteration order is deterministic.
    """
    result = []
    for row in rows:
        result.append((row[name_key], _money(row["total"]), str(row["count"])))
    return result


def build_csv_report(summary):
    """Build a deterministic, UTF-8 CSV export of a reports summary."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\r\n")

    writer.writerow(["Saamu Tailors - Business Report"])
    writer.writerow(["Generated at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["Report period", _format_range(summary["range"])])
    writer.writerow([])

    # Orders
    writer.writerow(["Orders"])
    writer.writerow(["Order Status", "Count"])
    distribution = summary["orders"]["status_distribution"]
    for status in ORDER_STATUS_ORDER:
        writer.writerow([status.label, str(distribution[status])])
    writer.writerow(["Total", str(distribution["total"])])
    writer.writerow(["Order revenue", _money(summary["orders"]["revenue"])])
    writer.writerow([])
    writer.writerow(["Garment Quantities"])
    writer.writerow(["Garment Type", "Quantity"])
    garment_quantities = summary["orders"]["garment_quantities"]
    if garment_quantities:
        for garment_type in sorted(garment_quantities):
            writer.writerow([garment_type, str(garment_quantities[garment_type])])
    else:
        writer.writerow(["-", "-"])
    writer.writerow([])

    # Customers
    writer.writerow(["Customers"])
    writer.writerow(["Metric", "Value"])
    for label, key in _CUSTOMER_METRICS:
        writer.writerow([label, str(_resolve(summary, key))])
    writer.writerow([])

    # Tailor workload
    writer.writerow(["Tailor Workload"])
    writer.writerow(["Metric", "Value"])
    for label, path, is_money in _WORKLOAD_METRICS:
        value = _resolve(summary, path)
        writer.writerow([label, _money(value) if is_money else str(value)])
    writer.writerow([])

    # Financial summary
    writer.writerow(["Financial Summary"])
    writer.writerow(["Metric", "Value"])
    for label, path, is_money in _FINANCIAL_METRICS:
        value = _resolve(summary, path)
        writer.writerow([label, _money(value) if is_money else str(value)])
    writer.writerow([])

    # Income by payment method / type
    writer.writerow(["Income by Payment Method"])
    writer.writerow(["Payment Method", "Total", "Count"])
    for row in _rows_for_breakdown(
        summary["financial"]["income"]["by_payment_method"], "payment_method"
    ):
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Income by Payment Type"])
    writer.writerow(["Payment Type", "Total", "Count"])
    for row in _rows_for_breakdown(
        summary["financial"]["income"]["by_payment_type"], "payment_type"
    ):
        writer.writerow(row)
    writer.writerow([])

    # Expenses by category / payment method
    writer.writerow(["Expenses by Category"])
    writer.writerow(["Category", "Total", "Count"])
    for row in _rows_for_breakdown(
        summary["financial"]["expenses"]["by_category"], "category"
    ):
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Expenses by Payment Method"])
    writer.writerow(["Payment Method", "Total", "Count"])
    for row in _rows_for_breakdown(
        summary["financial"]["expenses"]["by_payment_method"], "payment_method"
    ):
        writer.writerow(row)
    writer.writerow([])

    return output.getvalue().encode("utf-8")


def _resolve(data, path):
    """Resolve a dotted ``path`` such as ``financial.income.total_income``."""
    current = data
    for part in path.split("."):
        current = current[part]
    return current


def build_pdf_report(summary):
    """Build a human-readable, printable PDF snapshot of a reports summary.

    ``pageCompression=0`` keeps text visible in the raw byte stream so the
    export's content can be asserted directly in tests without a PDF parser.
    All strings are rendered as ASCII to avoid font-encoding surprises.
    """
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=A4, pageCompression=0)
    width, height = A4
    margin = 36
    right_edge = width - margin
    y = height - margin

    title_font = "Helvetica-Bold"
    section_font = "Helvetica-Bold"
    body_font = "Helvetica"

    def ensure_page(space):
        nonlocal y
        if y < margin + space:
            canvas.showPage()
            canvas.setFont(title_font, 9)
            canvas.drawString(
                margin,
                height - margin,
                "Saamu Tailors - Business Report (continued)",
            )
            y = height - margin - 18

    def draw_line(label, value):
        nonlocal y
        ensure_page(16)
        canvas.setFont(body_font, 10)
        canvas.drawString(margin, y, _to_ascii(label))
        canvas.setFont(body_font, 10)
        canvas.drawRightString(right_edge, y, _to_ascii(value))
        y -= 15

    def draw_section(title):
        nonlocal y
        ensure_page(18)
        y -= 4
        canvas.setFont(section_font, 11)
        canvas.drawString(margin, y, _to_ascii(title))
        y -= 6
        canvas.setLineWidth(0.5)
        canvas.line(margin, y, right_edge, y)
        y -= 14

    def money_label(value):
        return f"Rs {_money(value)}"

    canvas.setTitle("Saamu Tailors - Business Report")
    canvas.setFont(title_font, 16)
    canvas.drawString(margin, y, "Saamu Tailors - Business Report")
    y -= 22
    canvas.setFont(body_font, 9)
    canvas.drawString(
        margin, y, f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    y -= 13
    canvas.drawString(
        margin, y, f"Report period: {_to_ascii(_format_range(summary['range']))}"
    )
    y -= 20

    draw_section("Financial Summary")
    for label, path, is_money in _FINANCIAL_METRICS:
        value = _resolve(summary, path)
        draw_line(label, money_label(value) if is_money else str(value))

    draw_section("Orders")
    distribution = summary["orders"]["status_distribution"]
    for status in ORDER_STATUS_ORDER:
        draw_line(f"Orders - {status.label}", str(distribution[status]))
    draw_line("Orders - Total", str(distribution["total"]))
    draw_line("Order revenue", money_label(summary["orders"]["revenue"]))
    for garment_type in sorted(summary["orders"]["garment_quantities"]):
        draw_line(
            f"Garments - {garment_type}",
            str(summary["orders"]["garment_quantities"][garment_type]),
        )

    draw_section("Customers")
    for label, key in _CUSTOMER_METRICS:
        draw_line(label, str(_resolve(summary, key)))

    draw_section("Tailor Workload")
    for label, path, is_money in _WORKLOAD_METRICS:
        value = _resolve(summary, path)
        draw_line(label, money_label(value) if is_money else str(value))

    draw_section("Payroll & Settlements")
    draw_line(
        "Payroll paid in range", money_label(summary["financial"]["payroll_paid"])
    )
    draw_line(
        "Salary advances in range",
        money_label(summary["financial"]["salary_advances"]),
    )

    draw_section("Income by Payment Type")
    for row in _rows_for_breakdown(
        summary["financial"]["income"]["by_payment_type"], "payment_type"
    ):
        draw_line(row[0], f"{money_label(row[1])}  ({row[2]})")

    draw_section("Expenses by Category")
    for row in _rows_for_breakdown(
        summary["financial"]["expenses"]["by_category"], "category"
    ):
        draw_line(row[0], f"{money_label(row[1])}  ({row[2]})")

    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


def _to_ascii(value):
    """ASCII-safe text; transliterated where needed to avoid font issues."""
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value.encode("ascii", "replace").decode("ascii")
