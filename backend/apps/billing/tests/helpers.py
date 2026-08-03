"""Shared helpers for billing/invoice tests."""

from datetime import date
from decimal import Decimal

from apps.billing.models import CustomerPayment, Invoice, InvoiceItem
from apps.customers.tests.helpers import make_owner, make_staff  # noqa: F401
from apps.orders.models import Order, OrderItem
from apps.orders.tests.helpers import create_measurement


def invoice_list_url():
    return "/api/v1/invoices/"


def invoice_detail_url(invoice_id):
    return f"/api/v1/invoices/{invoice_id}/"


def invoice_payments_url(invoice_id):
    return f"/api/v1/invoices/{invoice_id}/payments/"


def order_invoice_url(order_id):
    return f"/api/v1/orders/{order_id}/invoice/"


def create_order(customer=None, **extra):
    """Create an order directly with two lines.

    Default lines: 2x SHIRT @ 100.00 and 1x PANT @ 250.50 -> total 450.50.
    """
    from apps.customers.tests.helpers import create_customer

    customer = customer or create_customer()
    shirt = create_measurement(customer, garment_type="SHIRT")
    pant = create_measurement(customer, garment_type="PANT")
    rows = [
        OrderItem(
            garment_type="SHIRT",
            quantity=2,
            unit_price=Decimal("100.00"),
            measurement=shirt,
        ),
        OrderItem(
            garment_type="PANT",
            quantity=1,
            unit_price=Decimal("250.50"),
            measurement=pant,
        ),
    ]
    total = sum((row.unit_price * row.quantity for row in rows), Decimal("0.00"))
    order = Order.objects.create(customer=customer, total_amount=total, **extra)
    for row in rows:
        row.order = order
    OrderItem.objects.bulk_create(rows)
    return order


def create_invoice(order=None, **extra):
    """Create an invoice with item snapshots copied from an order."""
    order = order or create_order()
    defaults = {
        "order": order,
        "invoice_date": date.today(),
        "subtotal": order.total_amount,
        "adjustment_amount": Decimal("0.00"),
        "total_amount": order.total_amount,
    }
    defaults.update(extra)
    invoice = Invoice.objects.create(**defaults)
    snapshots = []
    for item in order.items.all():
        snapshots.append(
            InvoiceItem(
                invoice=invoice,
                garment_type=item.get_garment_type_display(),
                garment_code=item.garment_type,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.unit_price * item.quantity,
            )
        )
    InvoiceItem.objects.bulk_create(snapshots)
    return invoice


def create_payment(invoice, amount="100.00", payment_date=None, method=None, **extra):
    """Create a customer payment directly against an invoice."""
    defaults = {
        "invoice": invoice,
        "amount": amount,
        "payment_date": payment_date or date.today(),
        "payment_method": method or CustomerPayment.Method.CASH,
    }
    defaults.update(extra)
    return CustomerPayment.objects.create(**defaults)
