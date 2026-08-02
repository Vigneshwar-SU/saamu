import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import Role
from apps.authentication.tests.helpers import make_user

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.urls("apps.authentication.tests.permission_urls"),
]

PASSWORD = "test-password-123"


def _auth(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


@pytest.fixture
def owner():
    return make_user(username="owner_p", role=Role.OWNER, password=PASSWORD)


@pytest.fixture
def staff():
    return make_user(username="staff_p", role=Role.STAFF, password=PASSWORD)


def test_anonymous_is_denied_on_staff_mutation(client):
    response = client.post("/_test/staff-only/", {}, content_type="application/json")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_anonymous_is_denied_on_read_endpoints(client):
    response = client.get("/_test/owner-or-staff/")
    assert response.status_code == 401
    response = client.get("/_test/authenticated-only/")
    assert response.status_code == 401


def test_owner_is_recognized(client, owner):
    response = client.get("/_test/owner-only/", **_auth(owner))
    assert response.status_code == 200


def test_staff_is_denied_on_owner_only_view(client, staff):
    response = client.get("/_test/owner-only/", **_auth(staff))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_owner_cannot_perform_protected_mutation(client, owner):
    response = client.post(
        "/_test/staff-only/", {}, content_type="application/json", **_auth(owner)
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_staff_receives_staff_authorization(client, staff):
    response = client.post(
        "/_test/staff-only/", {}, content_type="application/json", **_auth(staff)
    )
    assert response.status_code == 200


def test_owner_and_staff_can_read_shared_endpoint(client, owner, staff):
    assert client.get("/_test/owner-or-staff/", **_auth(owner)).status_code == 200
    assert client.get("/_test/owner-or-staff/", **_auth(staff)).status_code == 200


def test_owner_or_staff_permission_requires_valid_role(client, staff):
    staff.role = "MANAGER"
    staff.save(update_fields=["role"])
    response = client.get("/_test/owner-or-staff/", **_auth(staff))
    assert response.status_code == 403
