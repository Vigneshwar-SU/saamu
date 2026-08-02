import pytest

pytestmark = pytest.mark.django_db


def test_health_endpoint_returns_expected_response(client):
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["application"] == "Saamu Tailors"
    assert data["version"] == "1.0"


def test_health_endpoint_is_public(client):
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert "database" in response.json()
