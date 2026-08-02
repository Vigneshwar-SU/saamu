"""Customer archive/restore behavior tests (soft-delete, no physical delete)."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.customers.models import Customer
from apps.customers.tests.helpers import (
    create_customer,
    customer_archive_url,
    customer_detail_url,
    customer_list_url,
    customer_restore_url,
    make_staff,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(staff):
    from apps.authentication.tests.helpers import auth_header

    return {"HTTP_AUTHORIZATION": auth_header(staff)["HTTP_AUTHORIZATION"]}


def test_archive_retains_record(client, staff):
    customer = create_customer()
    assert Customer.objects.filter(pk=customer.pk).exists()

    response = client.post(customer_archive_url(customer.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["success"] is True

    # No physical deletion: the row still exists with is_active=False.
    assert Customer.objects.filter(pk=customer.pk).exists()
    customer.refresh_from_db()
    assert customer.is_active is False


def test_archived_customer_detail_is_still_accessible(client, staff):
    customer = create_customer()
    customer.is_active = False
    customer.save(update_fields=["is_active"])

    response = client.get(customer_detail_url(customer.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_archived_customer_removed_from_active_list(client, staff):
    customer = create_customer()
    response = client.post(customer_archive_url(customer.id), **_auth(staff))
    assert response.status_code == 200

    active = client.get(customer_list_url(), **_auth(staff))
    assert active.json()["count"] == 0

    archived = client.get(f"{customer_list_url()}?status=archived", **_auth(staff))
    assert archived.json()["count"] == 1


def test_archive_is_idempotent(client, staff):
    customer = create_customer()
    first = client.post(customer_archive_url(customer.id), **_auth(staff))
    second = client.post(customer_archive_url(customer.id), **_auth(staff))
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["success"] is True


def test_restore_reactivates_customer(client, staff):
    customer = create_customer()
    client.post(customer_archive_url(customer.id), **_auth(staff))

    response = client.post(customer_restore_url(customer.id), **_auth(staff))
    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.is_active is True

    active = client.get(customer_list_url(), **_auth(staff))
    assert active.json()["count"] == 1


def test_restore_is_idempotent(client, staff):
    customer = create_customer()
    response = client.post(customer_restore_url(customer.id), **_auth(staff))
    assert response.status_code == 200
    assert response.json()["message"] == "Customer is already active."


def test_archive_touches_updated_at(client, staff):
    customer = create_customer()
    customer.updated_at = timezone.now() - timedelta(days=1)
    customer.save(update_fields=["updated_at"])

    response = client.post(customer_archive_url(customer.id), **_auth(staff))
    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.updated_at > timezone.now() - timedelta(hours=1)
