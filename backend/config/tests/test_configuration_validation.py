"""Phase 20 tests for deployment configuration and production validation.

The helpers under test are pure functions over an environment mapping, so they
are exercised deterministically without mutating the process environment or
reloading Django's already-loaded settings.
"""

import pytest

from config.configuration_validation import (
    DEFAULT_DATABASE_ENGINE,
    DEFAULT_DATABASE_HOST,
    DEFAULT_DATABASE_NAME,
    DEFAULT_DATABASE_PASSWORD,
    DEFAULT_DATABASE_PORT,
    DEFAULT_DATABASE_USER,
    DEV_SECRET_KEY,
    build_database_config,
    production_validation_errors,
    validate_production_configuration,
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
# Environment-driven database configuration
# ---------------------------------------------------------------------------


def test_database_config_uses_local_defaults_without_environment():
    assert build_database_config({}) == {
        "ENGINE": DEFAULT_DATABASE_ENGINE,
        "NAME": DEFAULT_DATABASE_NAME,
        "USER": DEFAULT_DATABASE_USER,
        "PASSWORD": DEFAULT_DATABASE_PASSWORD,
        "HOST": DEFAULT_DATABASE_HOST,
        "PORT": DEFAULT_DATABASE_PORT,
    }


def test_database_engine_is_always_postgresql():
    assert build_database_config({})["ENGINE"] == "django.db.backends.postgresql"


def test_database_config_reads_environment_values():
    env = {
        "DATABASE_NAME": "saamu_cloud",
        "DATABASE_USER": "saamu_app",
        "DATABASE_PASSWORD": "cloud-password",
        "DATABASE_HOST": "db.cloud.example.com",
        "DATABASE_PORT": "5432",
    }
    config = build_database_config(env)
    assert config["NAME"] == "saamu_cloud"
    assert config["USER"] == "saamu_app"
    assert config["PASSWORD"] == "cloud-password"
    assert config["HOST"] == "db.cloud.example.com"
    assert config["PORT"] == "5432"


def test_settings_database_configuration_keeps_local_defaults():
    from django.conf import settings

    database = settings.DATABASES["default"]
    assert set(database) >= {"ENGINE", "NAME", "USER", "PASSWORD", "HOST", "PORT"}
    assert database["ENGINE"] == "django.db.backends.postgresql"
    assert database["NAME"]


# ---------------------------------------------------------------------------
# Production validation: development mode
# ---------------------------------------------------------------------------


def test_development_mode_never_errors_even_when_settings_missing():
    assert production_validation_errors({"DEBUG": "True"}) == []


def test_development_mode_never_errors_with_defaults():
    assert production_validation_errors({"DEBUG": "true"}) == []


# ---------------------------------------------------------------------------
# Production validation: missing / unsafe settings
# ---------------------------------------------------------------------------


def test_complete_production_configuration_is_valid():
    assert production_validation_errors(_production_env()) == []


def test_missing_secret_key_is_reported():
    errors = production_validation_errors(_production_env(SECRET_KEY=""))
    assert any("Secret key" in error for error in errors)


def test_development_secret_key_is_rejected_in_production():
    errors = production_validation_errors(_production_env(SECRET_KEY=DEV_SECRET_KEY))
    assert any("Secret key" in error for error in errors)


def test_missing_allowed_hosts_is_reported():
    errors = production_validation_errors(_production_env(ALLOWED_HOSTS=""))
    assert any("allowed host" in error for error in errors)


def test_blank_allowed_hosts_entry_is_reported():
    errors = production_validation_errors(_production_env(ALLOWED_HOSTS="  ,  "))
    assert any("allowed host" in error for error in errors)


def test_missing_database_name_is_reported():
    errors = production_validation_errors(_production_env(DATABASE_NAME=""))
    assert any("Database name" in error for error in errors)


def test_missing_database_user_is_reported():
    errors = production_validation_errors(_production_env(DATABASE_USER=""))
    assert any("Database user" in error for error in errors)


def test_missing_database_password_is_reported():
    errors = production_validation_errors(_production_env(DATABASE_PASSWORD=""))
    assert any("Database password" in error for error in errors)


def test_development_database_password_is_rejected_in_production():
    errors = production_validation_errors(
        _production_env(DATABASE_PASSWORD=DEFAULT_DATABASE_PASSWORD)
    )
    assert any("Database password" in error for error in errors)


def test_missing_database_host_is_reported():
    errors = production_validation_errors(_production_env(DATABASE_HOST=""))
    assert any("Database host" in error for error in errors)


def test_missing_database_port_is_reported():
    errors = production_validation_errors(_production_env(DATABASE_PORT=""))
    assert any("Database port" in error for error in errors)


def test_non_numeric_database_port_is_reported():
    errors = production_validation_errors(_production_env(DATABASE_PORT="abc"))
    assert any("Database port" in error for error in errors)


def test_all_missing_settings_report_every_category_in_order():
    env = {
        "DEBUG": "False",
        "SECRET_KEY": "",
        "ALLOWED_HOSTS": "",
        "DATABASE_NAME": "",
        "DATABASE_USER": "",
        "DATABASE_PASSWORD": "",
        "DATABASE_HOST": "",
        "DATABASE_PORT": "",
    }
    errors = production_validation_errors(env)
    assert len(errors) == 12
    assert "Secret key" in errors[0]
    assert "allowed host" in errors[1]
    assert "Database name" in errors[2]
    assert "Database user" in errors[3]
    assert "Database password" in errors[4]
    assert "Database host" in errors[5]
    assert "Database port" in errors[6]
    assert "Frontend URL" in errors[7]
    assert "Email host is required" in errors[8]
    assert "Email host user" in errors[9]
    assert "Email host password" in errors[10]
    assert "Default from email" in errors[11]


# ---------------------------------------------------------------------------
# Production validation: secret safety
# ---------------------------------------------------------------------------


def test_errors_never_contain_secret_values():
    env = {
        "DEBUG": "False",
        "SECRET_KEY": "top-secret-key-value",
        "DATABASE_PASSWORD": "top-secret-db-password",
        "ALLOWED_HOSTS": "",
    }
    joined = " ".join(production_validation_errors(env))
    assert "top-secret-key-value" not in joined
    assert "top-secret-db-password" not in joined


def test_errors_never_contain_connection_details():
    env = {
        "DEBUG": "False",
        "SECRET_KEY": "top-secret-key",
        "DATABASE_PASSWORD": "top-secret-password",
        "DATABASE_HOST": "db.cloud.example.com",
        "DATABASE_PORT": "5432",
        "DATABASE_NAME": "saamu_cloud",
        "DATABASE_USER": "saamu_app",
    }
    joined = " ".join(production_validation_errors(env))
    assert "db.cloud.example.com" not in joined
    assert "saamu_cloud" not in joined
    assert "saamu_app" not in joined


def test_validate_production_configuration_raises_without_values():
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured) as exc_info:
        validate_production_configuration(
            {
                "DEBUG": "False",
                "SECRET_KEY": "real-secret",
                "DATABASE_PASSWORD": "super-secret-password",
                "DATABASE_HOST": "",
            }
        )
    message = str(exc_info.value)
    assert "Database host" in message
    assert "super-secret-password" not in message
    assert "real-secret" not in message


def test_validate_production_configuration_is_noop_in_development():
    validate_production_configuration({"DEBUG": "True"})
