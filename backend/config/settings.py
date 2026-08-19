"""
Django settings for Saamu Tailors project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from .configuration_validation import (
    build_database_config,
    build_security_settings,
    default_renderer_classes,
    parse_bool,
    parse_non_negative_int,
    validate_production_configuration,
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# Ensure `apps` directory is in sys.path
import sys

sys.path.insert(0, str(BASE_DIR / "apps"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = os.getenv("SECRET_KEY", "")

DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes", "t")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]


# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party packages
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # Local apps
    "apps.authentication.apps.AuthenticationConfig",
    "apps.common.apps.CommonConfig",
    "apps.customers.apps.CustomersConfig",
    "apps.orders.apps.OrdersConfig",
    "apps.tailors.apps.TailorsConfig",
    "apps.attendance.apps.AttendanceConfig",
    "apps.payroll.apps.PayrollConfig",
    "apps.payments.apps.PaymentsConfig",
    "apps.finance.apps.FinanceConfig",
    "apps.billing.apps.BillingConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# PostgreSQL ONLY per strict requirement (no SQLite fallback).
# Connection values are environment-driven (Phase 20) via
# config/configuration_validation.build_database_config so the same codebase
# supports the local installation and a cloud-hosted PostgreSQL target. The
# defaults below exist for local development only and are rejected by the
# production validation below.
DATABASES = {
    "default": build_database_config(),
}

# Backup / restore storage (Phase 16). Defaults to a directory outside the
# application source tree (the user's home directory) and is overridable with
# BACKUP_DIR in backend/.env (e.g. D:\\SaamuBackups). Backup artifacts must
# never live inside the source repository.
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(Path.home() / "SaamuBackups")))

# Optional directory that contains the PostgreSQL client tools (pg_dump,
# pg_restore, psql). When empty the tools are located on PATH. Example for a
# local PostgreSQL 18 install: C:\\Program Files\\PostgreSQL\\18\\bin
PG_BIN = os.getenv("PGBIN", "").strip()

# Production configuration validation (Phase 20)
#
# All settings above are permissive by default for the local installation. In
# production mode (DEBUG=false) the deployment must provide every required
# database and host setting explicitly and must not use the development secret
# defaults. validate_production_configuration fails fast at startup with
# messages that name only the configuration category and never expose secret
# values, so an unsafe deployment cannot quietly start.
validate_production_configuration()


# Custom User Model
AUTH_USER_MODEL = "authentication.User"


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Kolkata")

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
# Paths are project-relative by default and environment-overridable for cloud deployment.

STATIC_URL = os.getenv("STATIC_URL", "static/")
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", str(BASE_DIR / "static")))

MEDIA_URL = os.getenv("MEDIA_URL", "media/")
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Secure by default: every API endpoint requires authentication unless
    # it explicitly opts out (e.g. health check, token endpoints).
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
    # JSON only in production; the browsable API is a development convenience.
    "DEFAULT_RENDERER_CLASSES": default_renderer_classes(),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    # Return numeric JSON values for DecimalFields (measurements) instead of
    # strings, so the frontend works with plain numbers.
    "COERCE_DECIMAL_TO_STRING": False,
    # Scoped throttle rates for the public password reset endpoints. Only
    # endpoints that opt in via throttle_classes use these; other APIs are
    # unaffected. Overridable per environment (e.g. for development/testing).
    "DEFAULT_THROTTLE_RATES": {
        "password_reset_request": os.getenv("PASSWORD_RESET_REQUEST_RATE", "5/hour"),
        "password_reset_confirm": os.getenv("PASSWORD_RESET_CONFIRM_RATE", "30/hour"),
    },
}

# SimpleJWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# Email configuration (Phase 22 - password reset)
#
# All values are environment-driven so the same codebase can send through
# Gmail SMTP in development and another provider in production without code
# changes. EMAIL_HOST_PASSWORD must only ever live in the local .env (Gmail
# requires an App Password); it is never read from source. With DEBUG=False the
# production validation below refuses to start until these are provided.
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = parse_non_negative_int(os.getenv("EMAIL_PORT", "")) or 587
EMAIL_USE_TLS = parse_bool(os.getenv("EMAIL_USE_TLS", ""), default=True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")

# Frontend base URL used to build password reset links in emails. Only the
# environment differs between development and production - never the code.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

# Password reset token lifetime in seconds (Django's built-in reset timeout).
# 900 seconds = 15 minutes. Invalid/empty environment values fall back to 900.
PASSWORD_RESET_TIMEOUT = parse_non_negative_int(
    os.getenv("PASSWORD_RESET_TIMEOUT", "")
) or 900

# CORS Configuration
# Origins are environment-driven. Local development defaults cover the Vite
# dev server origins (the Vite port may drift from 5173 when that port is
# already in use, so both 5173 and 5175 are included here and in .env.example).
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5175,http://127.0.0.1:5175",
    ).split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True


# Phase 21 security settings
#
# Secure cookies, HTTPS/HSTS behaviour and the proxy header are environment-
# driven so the same codebase runs locally over plain HTTP (secure cookies and
# HSTS off) and behind TLS in production. HSTS stays disabled (0 seconds)
# unless the operator explicitly enables it, because HSTS is only safe once the
# HTTPS/domain topology is ready. SECURE_PROXY_SSL_HEADER must only be enabled
# when the application really sits behind a TLS-terminating proxy.
SECURITY_SETTINGS = build_security_settings()

CSRF_TRUSTED_ORIGINS = SECURITY_SETTINGS["CSRF_TRUSTED_ORIGINS"]
SESSION_COOKIE_SECURE = SECURITY_SETTINGS["SESSION_COOKIE_SECURE"]
CSRF_COOKIE_SECURE = SECURITY_SETTINGS["CSRF_COOKIE_SECURE"]
SESSION_COOKIE_HTTPONLY = SECURITY_SETTINGS["SESSION_COOKIE_HTTPONLY"]
SESSION_COOKIE_SAMESITE = SECURITY_SETTINGS["SESSION_COOKIE_SAMESITE"]
SECURE_SSL_REDIRECT = SECURITY_SETTINGS["SECURE_SSL_REDIRECT"]
SECURE_HSTS_SECONDS = SECURITY_SETTINGS["SECURE_HSTS_SECONDS"]
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURITY_SETTINGS["SECURE_HSTS_INCLUDE_SUBDOMAINS"]
SECURE_HSTS_PRELOAD = SECURITY_SETTINGS["SECURE_HSTS_PRELOAD"]
SECURE_PROXY_SSL_HEADER = SECURITY_SETTINGS["SECURE_PROXY_SSL_HEADER"]
USE_X_FORWARDED_HOST = SECURITY_SETTINGS["USE_X_FORWARDED_HOST"]
# Always-on safe response headers (development and production).
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {module}:{lineno} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {name} {message}",
            "style": "{",
        },
    },
    "filters": {
        "sanitize_secrets": {
            "()": "config.logging_filters.SanitizeSecretsFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["sanitize_secrets"],
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "saamu.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "filters": ["sanitize_secrets"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "saamu": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "saamu.api": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
