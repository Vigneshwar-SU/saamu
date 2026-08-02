"""Shared helpers for order tests."""

from apps.customers.models import Customer, Measurement
from apps.customers.tests.helpers import create_customer as _create_customer
from apps.customers.tests.helpers import make_owner, make_staff  # noqa: F401


def order_list_url():
    return "/api/v1/orders/"


def order_detail_url(order_id):
    return f"/api/v1/orders/{order_id}/"


def order_status_url(order_id):
    return f"/api/v1/orders/{order_id}/status/"


def create_measurement(
    customer,
    garment_type="SHIRT",
    version=1,
    is_current=True,
    **values,
):
    """Create a measurement row for a customer with valid defaults."""
    defaults = {
        "neck_circumference": 15.5,
        "chest_circumference": 40.0,
        "waist_circumference": 34.0,
        "shoulder_width": 18.5,
        "sleeve_length": 25.0,
        "shirt_length": 30.0,
        "hip_circumference": 40.0,
        "length": 41.0,
    }
    defaults.update(values)
    return Measurement.objects.create(
        customer=customer,
        garment_type=garment_type,
        version=version,
        is_current=is_current,
        **defaults,
    )


def order_item_payload(garment_type="SHIRT", quantity=1, unit_price="100.00", **extra):
    payload = {
        "garment_type": garment_type,
        "quantity": quantity,
        "unit_price": unit_price,
    }
    payload.update(extra)
    return payload


def valid_order_payload(customer, items=None, **extra):
    """A valid order create payload for a customer.

    ``items`` is a list of ``order_item_payload`` dicts or garment codes.
    Existing measurements for each garment are reused when present; otherwise
    one is created and referenced by ``measurement_id``.
    """
    items = items or ["SHIRT"]
    item_payloads = []
    for garment in items:
        if isinstance(garment, str):
            measurement = Measurement.objects.filter(
                customer=customer, garment_type=garment
            ).first()
            if measurement is None:
                measurement = create_measurement(customer, garment_type=garment)
            item_payloads.append(
                order_item_payload(garment, measurement_id=measurement.id)
            )
        else:
            item_payloads.append(garment)
    payload = {
        "customer": customer.id,
        "items": item_payloads,
    }
    payload.update(extra)
    return payload
