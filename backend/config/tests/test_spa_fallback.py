"""Regression tests for the SPA fallback serving (config/spa.py)."""

import pytest
from django.test import override_settings


@pytest.fixture
def fake_frontend_dist(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html><body>SAAMU_SPA</body></html>", encoding="utf-8")
    return dist


def _body(response):
    if hasattr(response, "streaming_content"):
        return b"".join(response.streaming_content)
    return response.content


def test_spa_fallback_serves_built_index_html_for_frontend_route(client, fake_frontend_dist):
    with override_settings(FRONTEND_DIST=fake_frontend_dist):
        response = client.get("/customers")

    assert response.status_code == 200
    assert response["content-type"].startswith("text/html")
    assert b"SAAMU_SPA" in _body(response)


def test_spa_fallback_serves_index_html_for_nested_route(client, fake_frontend_dist):
    with override_settings(FRONTEND_DIST=fake_frontend_dist):
        response = client.get("/orders/123/details")

    assert response.status_code == 200
    assert b"SAAMU_SPA" in _body(response)


def test_spa_fallback_returns_404_when_build_missing(client):
    with override_settings(FRONTEND_DIST=None):
        response = client.get("/customers")
    assert response.status_code == 404


def test_api_namespace_is_not_intercepted_by_spa(client, fake_frontend_dist):
    with override_settings(FRONTEND_DIST=fake_frontend_dist):
        health = client.get("/api/v1/health/")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        unknown = client.get("/api/v1/does-not-exist/")
        assert unknown.status_code == 404
        assert b"SAAMU_SPA" not in _body(unknown)


def test_admin_and_media_prefixes_are_not_intercepted(client, fake_frontend_dist):
    with override_settings(FRONTEND_DIST=fake_frontend_dist):
        admin = client.get("/admin/login/")
        assert admin.status_code == 200
        assert b"SAAMU_SPA" not in _body(admin)

        media = client.get("/media/missing.png")
        assert media.status_code == 404
        assert b"SAAMU_SPA" not in _body(media)