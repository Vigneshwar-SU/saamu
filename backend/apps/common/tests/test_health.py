from unittest import mock

import pytest
from django.test import override_settings

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


def test_health_response_exposes_only_safe_fields(client):
    response = client.get("/api/v1/health/")
    data = response.json()
    assert set(data) == {"status", "application", "version", "database"}
    assert data["database"] in ("ok", "unavailable")
    assert "password" not in str(data).lower()
    assert "SECRET_KEY" not in str(data)


def test_health_database_failure_is_reported_safely(client, monkeypatch):
    from django.db import connection

    def _raise():
        raise RuntimeError("connection failed")

    monkeypatch.setattr(connection, "ensure_connection", _raise)
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"


def test_health_production_log_omits_exception_detail(client, monkeypatch):
    from django.db import connection

    from apps.common.views import logger as health_logger

    def _raise():
        raise RuntimeError("password=supersecret rejected")

    monkeypatch.setattr(connection, "ensure_connection", _raise)

    with override_settings(DEBUG=False):
        with mock.patch.object(health_logger, "error") as mock_error:
            response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"
    mock_error.assert_called_once()
    _, kwargs = mock_error.call_args
    assert kwargs.get("exc_info") is False


def test_health_development_log_keeps_exception_detail(client, monkeypatch):
    from django.db import connection

    from apps.common.views import logger as health_logger

    def _raise():
        raise RuntimeError("password=supersecret rejected")

    monkeypatch.setattr(connection, "ensure_connection", _raise)

    with override_settings(DEBUG=True):
        with mock.patch.object(health_logger, "error") as mock_error:
            response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"
    _, kwargs = mock_error.call_args
    assert kwargs.get("exc_info") is True
