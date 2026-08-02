from django.conf import settings


def test_database_engine_is_postgresql():
    engine = settings.DATABASES["default"]["ENGINE"]
    assert engine == "django.db.backends.postgresql"


def test_no_sqlite_fallback_configured():
    for config in settings.DATABASES.values():
        assert "sqlite" not in config["ENGINE"]


def test_default_permission_class_is_authenticated():
    permissions = settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]
    assert any("IsAuthenticated" in item for item in permissions)


def test_pagination_is_configured():
    assert settings.REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"]
    assert settings.REST_FRAMEWORK["PAGE_SIZE"] > 0


def test_exception_handler_is_configured():
    handler = settings.REST_FRAMEWORK["EXCEPTION_HANDLER"]
    assert handler == "apps.common.exceptions.api_exception_handler"


def test_jwt_installed_and_configured():
    assert "rest_framework_simplejwt" in settings.INSTALLED_APPS
    assert settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    assert settings.SIMPLE_JWT["AUTH_HEADER_TYPES"] == ("Bearer",)


def test_auth_user_model_configured():
    assert settings.AUTH_USER_MODEL == "authentication.User"


def test_cors_allowed_origins_configured():
    assert "http://localhost:5173" in settings.CORS_ALLOWED_ORIGINS
    assert "http://localhost:5175" in settings.CORS_ALLOWED_ORIGINS
    assert "http://127.0.0.1:5175" in settings.CORS_ALLOWED_ORIGINS


def test_api_namespace_is_versioned():
    from django.urls import resolve

    match = resolve("/api/v1/health/")
    assert match.url_name == "health-check"
    assert match.route.startswith("api/v1/")
