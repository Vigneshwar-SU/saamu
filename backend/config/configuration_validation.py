"""Deployment configuration helpers and production validation (Phase 20).

The database connection is environment-driven so the same codebase can target
either the local Windows/PostgreSQL installation or a cloud-hosted PostgreSQL
instance. Development defaults remain convenient (the local shop must keep
working unchanged); production is validated explicitly.

Safety rules honoured here:

- ``build_database_config`` reads connection values from the environment; it
  never hard-codes a host, a provider, or a filesystem path.
- ``production_validation_errors`` never includes a value in its messages. It
  names only the configuration *category* that is missing or unsafe, so the
  ``SECRET_KEY``, the database password and connection details can never leak
  through a configuration failure.
- Validation is a pure function over an environment mapping, deterministic,
  and only active in production mode (``DEBUG`` false). In development the
  list is always empty, so local defaults are never second-guessed.
"""

import os
from urllib.parse import urlsplit

DEFAULT_DATABASE_ENGINE = "django.db.backends.postgresql"
DEFAULT_DATABASE_NAME = "saamu_db"
DEFAULT_DATABASE_USER = "postgres"
DEFAULT_DATABASE_PASSWORD = "postgres"
DEFAULT_DATABASE_HOST = "localhost"
DEFAULT_DATABASE_PORT = "5432"

DEV_SECRET_KEY = "django-insecure-saamu-tailors-dev-key-change-in-production-123456"

TRUTHY_VALUES = ("true", "1", "yes", "t")

DEFAULT_SESSION_COOKIE_SAMESITE = "Lax"

_SESSION_COOKIE_SAMESITE_CHOICES = ("Lax", "Strict", "None")


# ---------------------------------------------------------------------------
# Environment value parsing (Phase 21)
# ---------------------------------------------------------------------------


def parse_comma_separated(value):
    """Split a comma-separated environment value into a cleaned list."""
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def parse_bool(value, default=False):
    """Interpret an environment variable as a boolean.

    Empty values (including empty strings injected by ``load_dotenv``) fall
    back to ``default`` so an unset variable behaves exactly like a missing
    one.
    """
    value = (value or "").strip().lower()
    if not value:
        return default
    return value in TRUTHY_VALUES


def parse_non_negative_int(value, default=0):
    """Parse a non-negative integer environment value; invalid input → default."""
    value = (value or "").strip()
    if not value.isdigit():
        return default
    return int(value)


def _is_absolute_http_origin(origin):
    """Whether ``origin`` is ``scheme://host[:port]`` with no path."""
    try:
        parsed = urlsplit(origin)
    except ValueError:
        return False
    return (
        parsed.scheme in ("http", "https") and bool(parsed.hostname) and not parsed.path
    )


def _is_loopback_origin(origin):
    """Whether an origin uses a loopback host (localhost / 127.x / ::1)."""
    host = (urlsplit(origin).hostname or "").lower()
    return host in ("localhost", "::1", "0.0.0.0") or host.startswith("127.")


def build_security_settings(env=None):
    """Return environment-driven Django security settings (Phase 21).

    Local development keeps its convenient HTTP defaults (secure cookies and
    HSTS off, no proxy header). Production values are read from the
    environment so the same codebase is safe behind a TLS-terminating
    deployment without hard-coding a topology. HSTS stays disabled (0
    seconds) until the operator explicitly enables it, because enabling HSTS
    before the HTTPS/domain topology is ready would be unsafe.
    """
    env = env if env is not None else os.environ
    samesite = (
        env.get("SESSION_COOKIE_SAMESITE", "").strip()
        or DEFAULT_SESSION_COOKIE_SAMESITE
    )
    if samesite not in _SESSION_COOKIE_SAMESITE_CHOICES:
        samesite = DEFAULT_SESSION_COOKIE_SAMESITE
    return {
        "CSRF_TRUSTED_ORIGINS": parse_comma_separated(
            env.get("CSRF_TRUSTED_ORIGINS", "")
        ),
        "SESSION_COOKIE_SECURE": parse_bool(env.get("SESSION_COOKIE_SECURE", "")),
        "CSRF_COOKIE_SECURE": parse_bool(env.get("CSRF_COOKIE_SECURE", "")),
        "SESSION_COOKIE_HTTPONLY": parse_bool(
            env.get("SESSION_COOKIE_HTTPONLY", ""), default=True
        ),
        "SESSION_COOKIE_SAMESITE": samesite,
        "SECURE_SSL_REDIRECT": parse_bool(env.get("SECURE_SSL_REDIRECT", "")),
        "SECURE_HSTS_SECONDS": parse_non_negative_int(
            env.get("SECURE_HSTS_SECONDS", "")
        ),
        "SECURE_HSTS_INCLUDE_SUBDOMAINS": parse_bool(
            env.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "")
        ),
        "SECURE_HSTS_PRELOAD": parse_bool(env.get("SECURE_HSTS_PRELOAD", "")),
        "SECURE_PROXY_SSL_HEADER": (
            ("HTTP_X_FORWARDED_PROTO", "https")
            if parse_bool(env.get("SECURE_PROXY_SSL_HEADER", ""))
            else None
        ),
        "USE_X_FORWARDED_HOST": parse_bool(env.get("USE_X_FORWARDED_HOST", "")),
    }


def default_renderer_classes(env=None):
    """DRF default renderers for the current environment.

    JSON only in production so no browsable API surface exists there; the
    browsable API is added back in development for convenience.
    """
    env = env if env is not None else os.environ
    renderers = ["rest_framework.renderers.JSONRenderer"]
    if _is_debug(env):
        renderers.append("rest_framework.renderers.BrowsableAPIRenderer")
    return tuple(renderers)


def _is_debug(env):
    """Whether the environment is in development (DEBUG resolves to true)."""
    return env.get("DEBUG", "True").strip().lower() in TRUTHY_VALUES


def build_database_config(env=None):
    """Return the Django ``DATABASES["default"]`` dictionary from ``env``.

    ``env`` defaults to ``os.environ``. PostgreSQL is the only supported
    engine. Every connection value is overridable through environment
    variables; the defaults below exist for the local installation only and
    are explicitly rejected by :func:`production_validation_errors`.
    """
    env = env if env is not None else os.environ
    return {
        "ENGINE": DEFAULT_DATABASE_ENGINE,
        "NAME": env.get("DATABASE_NAME", DEFAULT_DATABASE_NAME),
        "USER": env.get("DATABASE_USER", DEFAULT_DATABASE_USER),
        "PASSWORD": env.get("DATABASE_PASSWORD", DEFAULT_DATABASE_PASSWORD),
        "HOST": env.get("DATABASE_HOST", DEFAULT_DATABASE_HOST),
        "PORT": env.get("DATABASE_PORT", DEFAULT_DATABASE_PORT),
    }


def production_validation_errors(env=None):
    """Return the ordered list of production configuration problems.

    ``env`` defaults to ``os.environ``. In development mode (DEBUG truthy) the
    list is always empty so the local defaults are never validated. In
    production mode each required setting must be provided explicitly and the
    secret values must not be the development defaults.

    Every message names only the configuration category; secret values are
    never included.
    """
    env = env if env is not None else os.environ
    if _is_debug(env):
        return []

    errors = []

    secret_key = env.get("SECRET_KEY", "")
    if not secret_key or secret_key == DEV_SECRET_KEY:
        errors.append(
            "Secret key is required in production and must not be the "
            "development default."
        )

    allowed_hosts = [
        host.strip() for host in env.get("ALLOWED_HOSTS", "").split(",") if host.strip()
    ]
    if not allowed_hosts:
        errors.append("At least one allowed host is required in production.")

    if not env.get("DATABASE_NAME", ""):
        errors.append("Database name is required in production.")

    if not env.get("DATABASE_USER", ""):
        errors.append("Database user is required in production.")

    database_password = env.get("DATABASE_PASSWORD", "")
    if not database_password or database_password == DEFAULT_DATABASE_PASSWORD:
        errors.append(
            "Database password is required in production and must not be the "
            "development default."
        )

    if not env.get("DATABASE_HOST", ""):
        errors.append("Database host is required in production.")

    database_port = env.get("DATABASE_PORT", "")
    if not database_port or not database_port.strip().isdigit():
        errors.append("Database port is required in production and must be numeric.")

    for origin in parse_comma_separated(env.get("CSRF_TRUSTED_ORIGINS", "")):
        if not _is_absolute_http_origin(origin):
            errors.append(
                "CSRF trusted origins must be absolute origins "
                "(scheme://host[:port]) without a path."
            )
            break

    cors_origins = parse_comma_separated(env.get("CORS_ALLOWED_ORIGINS", ""))
    for origin in cors_origins:
        if not _is_absolute_http_origin(origin):
            errors.append(
                "CORS allowed origins must be absolute origins "
                "(scheme://host[:port]) without a path."
            )
            break
    if any(_is_loopback_origin(origin) for origin in cors_origins):
        errors.append(
            "CORS allowed origins must not use localhost or loopback hosts "
            "in production."
        )

    frontend_url = env.get("FRONTEND_URL", "").strip()
    if not frontend_url:
        errors.append(
            "Frontend URL is required in production (password reset links)."
        )
    elif not _is_absolute_http_origin(frontend_url):
        errors.append(
            "Frontend URL must be an absolute http(s) URL without a path."
        )
    elif _is_loopback_origin(frontend_url):
        errors.append(
            "Frontend URL must not use localhost or loopback hosts in production."
        )

    if not env.get("EMAIL_HOST", ""):
        errors.append("Email host is required in production.")
    if not env.get("EMAIL_HOST_USER", ""):
        errors.append("Email host user is required in production.")
    if not env.get("EMAIL_HOST_PASSWORD", ""):
        errors.append("Email host password is required in production.")
    if not env.get("DEFAULT_FROM_EMAIL", ""):
        errors.append("Default from email is required in production.")

    return errors


def validate_production_configuration(env=None):
    """Raise ``ImproperlyConfigured`` when production configuration is invalid.

    Called from ``config/settings.py`` so an unsafe production deployment fails
    fast at startup instead of running with defaults. Never raises in
    development mode. Errors name only configuration categories.
    """
    from django.core.exceptions import ImproperlyConfigured

    errors = production_validation_errors(env)
    if errors:
        raise ImproperlyConfigured(
            "Production configuration is invalid: " + "; ".join(errors)
        )
