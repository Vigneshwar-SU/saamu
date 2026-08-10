"""Phase 21 tests for production-hardening security configuration.

Coverage: environment parsing helpers, environment-driven Django security
settings, production-only JSON renderers, and production validation of CSRF /
CORS origins. Like the Phase 20 validation tests, these exercise pure helpers
over an environment mapping so they are deterministic and never mutate the
process environment or reload Django's loaded settings.
"""

import pytest

from config.configuration_validation import (
    build_security_settings,
    default_renderer_classes,
    parse_bool,
    parse_comma_separated,
    parse_non_negative_int,
    production_validation_errors,
)


def _production_env(**overrides):
    env = {
        "DEBUG": "False",
        "SECRET_KEY": "a-real-production-secret-key",
        "ALLOWED_HOSTS": "saamu.example.com",
        "DATABASE_NAME": "saamu_cloud",
        "DATABASE_USER": "saamu_app",
        "DATABASE_PASSWORD": "a-real-database-password",
        "DATABASE_HOST": "db.saamu.example.com",
        "DATABASE_PORT": "5432",
        "FRONTEND_URL": "https://saamu.example.com",
        "EMAIL_HOST": "smtp.gmail.com",
        "EMAIL_HOST_USER": "saamutailors1954@gmail.com",
        "EMAIL_HOST_PASSWORD": "a-real-app-password",
        "DEFAULT_FROM_EMAIL": "Saamu Tailors <saamutailors1954@gmail.com>",
    }
    env.update(overrides)
    return env


# ---------------------------------------------------------------------------
# Environment value parsing
# ---------------------------------------------------------------------------


def test_parse_comma_separated_splits_and_strips():
    assert parse_comma_separated(" a, b ,  ,c ") == ["a", "b", "c"]


def test_parse_comma_separated_empty():
    assert parse_comma_separated("") == []
    assert parse_comma_separated(None) == []
    assert parse_comma_separated("  ,  ") == []


@pytest.mark.parametrize("value", ["true", "True", "1", "yes", "t", "YES"])
def test_parse_bool_truthy(value):
    assert parse_bool(value) is True


@pytest.mark.parametrize("value", ["false", "0", "no", "n", "off", "whatever"])
def test_parse_bool_falsy(value):
    assert parse_bool(value) is False


def test_parse_bool_empty_uses_default():
    assert parse_bool("", default=True) is True
    assert parse_bool(None, default=False) is False


def test_parse_non_negative_int():
    assert parse_non_negative_int("31536000") == 31536000
    assert parse_non_negative_int("") == 0
    assert parse_non_negative_int("abc") == 0


# ---------------------------------------------------------------------------
# build_security_settings
# ---------------------------------------------------------------------------


def test_security_settings_defaults_for_local_development():
    settings = build_security_settings({})
    assert settings["CSRF_TRUSTED_ORIGINS"] == []
    assert settings["SESSION_COOKIE_SECURE"] is False
    assert settings["CSRF_COOKIE_SECURE"] is False
    assert settings["SESSION_COOKIE_HTTPONLY"] is True
    assert settings["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert settings["SECURE_SSL_REDIRECT"] is False
    assert settings["SECURE_HSTS_SECONDS"] == 0
    assert settings["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is False
    assert settings["SECURE_HSTS_PRELOAD"] is False
    assert settings["SECURE_PROXY_SSL_HEADER"] is None
    assert settings["USE_X_FORWARDED_HOST"] is False


def test_security_settings_read_production_environment():
    settings = build_security_settings(
        {
            "CSRF_TRUSTED_ORIGINS": "https://app.saamu.example.com",
            "SESSION_COOKIE_SECURE": "True",
            "CSRF_COOKIE_SECURE": "True",
            "SECURE_SSL_REDIRECT": "True",
            "SECURE_HSTS_SECONDS": "31536000",
            "SECURE_HSTS_INCLUDE_SUBDOMAINS": "True",
            "SECURE_HSTS_PRELOAD": "True",
            "SECURE_PROXY_SSL_HEADER": "True",
        }
    )
    assert settings["CSRF_TRUSTED_ORIGINS"] == ["https://app.saamu.example.com"]
    assert settings["SESSION_COOKIE_SECURE"] is True
    assert settings["CSRF_COOKIE_SECURE"] is True
    assert settings["SECURE_SSL_REDIRECT"] is True
    assert settings["SECURE_HSTS_SECONDS"] == 31536000
    assert settings["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is True
    assert settings["SECURE_HSTS_PRELOAD"] is True
    assert settings["SECURE_PROXY_SSL_HEADER"] == ("HTTP_X_FORWARDED_PROTO", "https")


def test_invalid_session_cookie_samesite_falls_back_to_lax():
    assert (
        build_security_settings({"SESSION_COOKIE_SAMESITE": "Bogus"})[
            "SESSION_COOKIE_SAMESITE"
        ]
        == "Lax"
    )
    assert (
        build_security_settings({"SESSION_COOKIE_SAMESITE": "Strict"})[
            "SESSION_COOKIE_SAMESITE"
        ]
        == "Strict"
    )


# ---------------------------------------------------------------------------
# Settings-level security configuration (development mode loaded by tests)
# ---------------------------------------------------------------------------


def test_settings_apply_security_defaults():
    from django.conf import settings

    assert settings.CSRF_TRUSTED_ORIGINS == []
    assert settings.SESSION_COOKIE_SECURE is False
    assert settings.CSRF_COOKIE_SECURE is False
    assert settings.SECURE_HSTS_SECONDS == 0
    assert settings.SECURE_PROXY_SSL_HEADER is None
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings.SECURE_REFERRER_POLICY == "same-origin"
    assert settings.X_FRAME_OPTIONS == "DENY"
    assert settings.SESSION_COOKIE_HTTPONLY is True


# ---------------------------------------------------------------------------
# Renderers: JSON-only in production
# ---------------------------------------------------------------------------


def test_renderers_include_browsable_api_in_development():
    renderers = default_renderer_classes({"DEBUG": "True"})
    assert "rest_framework.renderers.JSONRenderer" in renderers
    assert "rest_framework.renderers.BrowsableAPIRenderer" in renderers


def test_renderers_are_json_only_in_production():
    renderers = default_renderer_classes({"DEBUG": "False"})
    assert renderers == ("rest_framework.renderers.JSONRenderer",)


def test_settings_renderers_include_json_in_development():
    from django.conf import settings

    assert (
        "rest_framework.renderers.JSONRenderer"
        in settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]
    )


# ---------------------------------------------------------------------------
# Production validation: CSRF / CORS origins
# ---------------------------------------------------------------------------


def test_valid_production_origins_pass_validation():
    env = _production_env(
        CSRF_TRUSTED_ORIGINS="https://app.saamu.example.com,https://saamu.example.com",
        CORS_ALLOWED_ORIGINS="https://saamu.example.com",
    )
    assert production_validation_errors(env) == []


def test_csrf_origin_without_scheme_is_rejected():
    errors = production_validation_errors(
        _production_env(CSRF_TRUSTED_ORIGINS="saamu.example.com")
    )
    assert any("CSRF trusted origins" in error for error in errors)


def test_csrf_origin_with_path_is_rejected():
    errors = production_validation_errors(
        _production_env(CSRF_TRUSTED_ORIGINS="https://saamu.example.com/path")
    )
    assert any("CSRF trusted origins" in error for error in errors)


def test_cors_origin_without_scheme_is_rejected():
    errors = production_validation_errors(
        _production_env(CORS_ALLOWED_ORIGINS="app.example.com")
    )
    assert any("CORS allowed origins" in error for error in errors)


def test_cors_origin_with_path_is_rejected():
    errors = production_validation_errors(
        _production_env(CORS_ALLOWED_ORIGINS="https://app.example.com/path")
    )
    assert any("CORS allowed origins" in error for error in errors)


def test_localhost_cors_origin_is_rejected_in_production():
    errors = production_validation_errors(
        _production_env(CORS_ALLOWED_ORIGINS="http://localhost:5173")
    )
    assert any("localhost or loopback" in error for error in errors)


def test_loopback_ip_cors_origin_is_rejected_in_production():
    errors = production_validation_errors(
        _production_env(CORS_ALLOWED_ORIGINS="http://127.0.0.1:5173")
    )
    assert any("localhost or loopback" in error for error in errors)


def test_mixed_cors_origins_reject_loopback_and_report_real_origins_only():
    errors = production_validation_errors(
        _production_env(
            CORS_ALLOWED_ORIGINS="https://app.example.com,http://localhost:5173"
        )
    )
    assert any("localhost or loopback" in error for error in errors)
    assert "app.example.com" not in " ".join(errors)
