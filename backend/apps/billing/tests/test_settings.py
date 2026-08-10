"""Phase 22 Settings module - ShopDetails API tests.

The Settings UI reads and updates the database-backed ``ShopDetails`` singleton
through a single authoritative endpoint. OWNER is view-only; STAFF manages the
shop profile. Validation is server-authoritative so the shop block on the
digital bill can never show an empty name or an implausible year.
"""

import pytest

from apps.billing.models import ShopDetails
from apps.billing.tests.helpers import (
    create_invoice,
    create_order,
    invoice_bill_url,
    make_owner,
    make_staff,
)
from apps.customers.tests.helpers import auth_header

pytestmark = pytest.mark.django_db

SHOP_DETAILS_URL = "/api/v1/settings/shop-details/"


def _auth(user):
    return {"HTTP_AUTHORIZATION": auth_header(user)["HTTP_AUTHORIZATION"]}


def _payload(**overrides):
    payload = {
        "name": "Saamu Tailors",
        "tagline": "Precision tailoring since 1954",
        "address": "12 Gandhi Market, Bengaluru",
        "phone": "+91 9876543210",
        "established_year": 1954,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def owner():
    return make_owner()


@pytest.fixture
def staff():
    return make_staff()


def test_anonymous_cannot_read_or_update(client):
    assert client.get(SHOP_DETAILS_URL).status_code == 401
    response = client.put(
        SHOP_DETAILS_URL,
        data=_payload(),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_owner_can_read_shop_details(client, owner):
    response = client.get(SHOP_DETAILS_URL, **_auth(owner))
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {
        "id",
        "name",
        "tagline",
        "address",
        "phone",
        "established_year",
        "customer_follow_up_months",
    }
    assert data["name"] == "Saamu Tailors"
    assert data["established_year"] == 1954


def test_owner_cannot_update_shop_details(client, owner):
    response = client.put(
        SHOP_DETAILS_URL,
        data=_payload(name="Saamu Tailors & Co"),
        content_type="application/json",
        **_auth(owner),
    )
    assert response.status_code == 403
    assert ShopDetails.shop_details().name == "Saamu Tailors"


def test_staff_can_update_shop_details(client, staff):
    response = client.put(
        SHOP_DETAILS_URL,
        data=_payload(name="Saamu Tailors & Co", tagline="Crafted in Bengaluru"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Saamu Tailors & Co"
    assert data["tagline"] == "Crafted in Bengaluru"

    details = ShopDetails.shop_details()
    assert details.name == "Saamu Tailors & Co"
    assert details.tagline == "Crafted in Bengaluru"


def test_staff_update_keeps_singleton_single_row(client, staff):
    response = client.put(
        SHOP_DETAILS_URL,
        data=_payload(phone="+91 9000000000"),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 200
    assert ShopDetails.objects.count() == 1
    assert ShopDetails.shop_details().phone == "+91 9000000000"


def test_updated_shop_details_flow_to_bill(client, staff):
    invoice = create_invoice(create_order())
    client.put(
        SHOP_DETAILS_URL,
        data=_payload(address="1 Custom Lane, Bengaluru"),
        content_type="application/json",
        **_auth(staff),
    )
    response = client.get(invoice_bill_url(invoice.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["bill"]["shop"]["address"] == "1 Custom Lane, Bengaluru"


def test_update_requires_valid_name(client, staff):
    response = client.put(
        SHOP_DETAILS_URL,
        data=_payload(name="   "),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "name" in response.json()["error"]["details"]


def test_update_rejects_implausible_year(client, staff):
    response = client.put(
        SHOP_DETAILS_URL,
        data=_payload(established_year=5),
        content_type="application/json",
        **_auth(staff),
    )
    assert response.status_code == 400
    assert "established_year" in response.json()["error"]["details"]
