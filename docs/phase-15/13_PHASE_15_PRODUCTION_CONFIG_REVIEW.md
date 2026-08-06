# Phase 15 — Production Configuration Review

Status: **DONE** (review completed and documented; the local deployment remains a
development-mode environment until the checklist below is applied).

## 1. Scope

Review of `backend/config/settings.py`, `backend/.env` / `.env.example`, CORS,
authentication (JWT), error handling, pagination and logging to confirm that the
application has **no development-only behavior baked into production**, and that
the configuration is environment-driven and secret-safe.

## 2. Findings

### 2.1 Environment-driven configuration (good)

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, database credentials, `TIME_ZONE`,
  `LOG_LEVEL`, `LOG_DIR`, `STATIC_*`, `MEDIA_*` and `CORS_ALLOWED_ORIGINS` are
  all read from environment variables in `config/settings.py:24-38,102-110,153-157,207-214`.
- No secrets are committed. `.env` is gitignored (verified); `.env.example`
  ships placeholder values with an explicit "change in real deployment" comment.
- Database is PostgreSQL-only (`config/settings.py:102-111`); there is no
  SQLite fallback.

### 2.2 API security posture (good)

- DRF `DEFAULT_PERMISSION_CLASSES = IsAuthenticated` — every endpoint requires
  authentication unless it explicitly opts out (health check, token endpoints).
- Custom exception handler (`apps.common.exceptions.api_exception_handler`)
  normalizes every error to the standard
  `{success:false, error:{code, message, details?}}` contract and never leaks
  internal exception details.
- Pagination is on by default (`PAGE_SIZE = 20`).
- JWT: 60-minute access token, 1-day refresh, HS256, signing key derived from
  `SECRET_KEY` (`config/settings.py:194-201`).

### 2.3 Middleware (adequate for the target local-shop deployment)

- `SecurityMiddleware`, `XFrameOptionsMiddleware`, `CsrfViewMiddleware` and the
  standard session/authentication middleware are enabled
  (`config/settings.py:68-77`).
- HTTPS-only flags (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
  `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`) are not set. This is **correct
  for the current single-PC shop deployment over LAN HTTP**, and is a required
  change only if the app is ever exposed over the public internet or HTTPS.

### 2.4 Logging (good)

- Root logger to console, `django`/`saamu`/`saamu.api` to a rotating file
  (5 MB × 5 backups) under `backend/logs/` (`config/settings.py:219-265`).
- `LOG_DIR` auto-created and env-overridable.

### 2.5 Issues to address at production deploy time (not blocking local use)

| # | Finding | Current state | Required for production |
|---|---------|---------------|-------------------------|
| 1 | `SECRET_KEY` is the dev placeholder | `.env` and settings default both use the dev key | Set a unique random key (e.g. `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) in `.env` before real data goes in |
| 2 | `DEBUG=True` | `.env` sets `DEBUG=True` | Set `DEBUG=False` in `.env` (also flips the Browsable API renderer behavior only insofar as DRF serves the API; errors stop showing stack traces) |
| 3 | `ALLOWED_HOSTS` includes `0.0.0.0` | `.env` sets `localhost,127.0.0.1,0.0.0.0` | `0.0.0.0` is not a valid Host header; list only real hostnames/IPs, e.g. `localhost,127.0.0.1,192.168.1.50` for a LAN PC |
| 4 | `CORS_ALLOWED_ORIGINS` list | explicit dev origins (5173/5175) | Add the LAN host origin used by the deployed frontend; keep it explicit (no `*`) |
| 5 | HTTPS flags unset | disabled | Only needed if serving over HTTPS/public internet |
| 6 | DB password in `.env` | local `postgres` role | Keep the password out of version control (already gitignored) and rotate it if the machine is shared |

## 3. No code change required

This review concluded that `config/settings.py` is already correctly structured
for production (env-driven, secure-by-default API, no hardcoded secrets, no
SQLite fallback, explicit CORS). The items in section 2.5 are **operator
actions applied to `.env` at deploy time**, not code changes — so no backend
behavior was modified for this review and no regression surface was introduced.

## 4. Verification performed

- `python manage.py check` — System check identified no issues.
- Confirmed `.env` is ignored by git and `.env.example` contains only
  placeholders.
- Confirmed DRF default permission is `IsAuthenticated` and the custom
  exception handler is wired as the global handler.
- Confirmed no `DEBUG`-dependent or platform-specific branches exist in the
  settings module.
