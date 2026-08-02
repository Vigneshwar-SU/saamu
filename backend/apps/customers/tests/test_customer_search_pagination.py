"""Customer search, pagination, and status-filter tests."""

import pytest

from apps.customers.tests.helpers import (
    create_customer,
    customer_list_url,
    make_staff,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return make_staff()


def _auth(staff):
    from apps.authentication.tests.helpers import auth_header

    return {"HTTP_AUTHORIZATION": auth_header(staff)["HTTP_AUTHORIZATION"]}


def _list(client, staff, query=""):
    return client.get(f"{customer_list_url()}?{query}", **_auth(staff))


def test_search_by_name_is_case_insensitive(client, staff):
    create_customer(full_name="Ravi Kumar", mobile_number="9000000001")
    create_customer(full_name="Meena Ravi", mobile_number="9000000002")
    create_customer(full_name="Suresh", mobile_number="9000000003")

    response = _list(client, staff, "search=ravi")
    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()["results"]]
    assert set(names) == {"Ravi Kumar", "Meena Ravi"}


def test_search_by_mobile(client, staff):
    create_customer(full_name="A", mobile_number="9000000001")
    create_customer(full_name="B", mobile_number="9000000002")
    create_customer(full_name="C", mobile_number="9000000003")

    response = _list(client, staff, "search=0002")
    assert response.status_code == 200
    assert [item["full_name"] for item in response.json()["results"]] == ["B"]


def test_search_by_id(client, staff):
    first = create_customer(full_name="Alpha", mobile_number="9000000001")
    create_customer(full_name="Beta", mobile_number="9000000002")

    response = _list(client, staff, f"search={first.id}")
    assert response.status_code == 200
    assert [item["full_name"] for item in response.json()["results"]] == ["Alpha"]


def test_search_with_no_match_returns_empty(client, staff):
    create_customer(full_name="Ravi", mobile_number="9000000001")
    response = _list(client, staff, "search=zzzznothing")
    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["results"] == []


def test_active_status_is_the_default_filter(client, staff):
    create_customer(full_name="Active One", mobile_number="9000000001")
    archived = create_customer(full_name="Archived One", mobile_number="9000000002")
    archived.is_active = False
    archived.save(update_fields=["is_active"])

    response = _list(client, staff, "")
    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()["results"]]
    assert names == ["Active One"]


def test_archived_filter_returns_only_archived(client, staff):
    create_customer(full_name="Active One", mobile_number="9000000001")
    archived = create_customer(full_name="Archived One", mobile_number="9000000002")
    archived.is_active = False
    archived.save(update_fields=["is_active"])

    response = _list(client, staff, "status=archived")
    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()["results"]]
    assert names == ["Archived One"]
    assert all(item["is_active"] is False for item in response.json()["results"])


def test_all_status_returns_both(client, staff):
    create_customer(full_name="Active One", mobile_number="9000000001")
    archived = create_customer(full_name="Archived One", mobile_number="9000000002")
    archived.is_active = False
    archived.save(update_fields=["is_active"])

    response = _list(client, staff, "status=all")
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_pagination_returns_first_page(client, staff):
    for index in range(25):
        create_customer(
            full_name=f"Customer {index:02d}", mobile_number=f"900000{index:04d}"
        )

    response = _list(client, staff, "")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 25
    assert len(data["results"]) == 20
    assert data["next"] is not None
    assert data["previous"] is None


def test_pagination_second_page(client, staff):
    for index in range(25):
        create_customer(
            full_name=f"Customer {index:02d}", mobile_number=f"900000{index:04d}"
        )

    response = _list(client, staff, "page=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 5
    assert data["next"] is None
    assert data["previous"] is not None
