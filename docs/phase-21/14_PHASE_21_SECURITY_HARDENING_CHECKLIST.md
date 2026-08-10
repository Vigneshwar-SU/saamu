# Phase 21 — Security Hardening Checklist

## Django Core
- [ ] `DEBUG=False` in production.
- [ ] Production `SECRET_KEY` is supplied externally.
- [ ] Development/default secret is rejected in production.
- [ ] `ALLOWED_HOSTS` is explicit and non-empty.
- [ ] `CSRF_TRUSTED_ORIGINS` is explicit where HTTPS cross-origin deployment requires it.
- [ ] CORS is restricted to known frontend origins when enabled.
- [ ] `SESSION_COOKIE_SECURE` is correct for HTTPS.
- [ ] `CSRF_COOKIE_SECURE` is correct for HTTPS.
- [ ] Appropriate `SECURE_*` settings are reviewed for the deployment topology.
- [ ] HSTS is enabled only when the HTTPS/domain topology is ready.

## Authentication & Authorization
- [ ] OWNER/STAFF RBAC remains backend-authoritative.
- [ ] Anonymous access is not accidentally expanded.
- [ ] No administrative/destructive endpoint is exposed to browser users.

## API Security
- [ ] Error responses do not leak tracebacks.
- [ ] Health endpoint contains no secrets.
- [ ] No credentials appear in API responses.
- [ ] No arbitrary command/path endpoint exists.

## Data & Privacy
- [ ] Customer phone numbers are not unnecessarily logged.
- [ ] Internal notes are not leaked through communication/reminder outputs.
- [ ] Database credentials are not logged.
- [ ] Backups remain outside the source tree.
- [ ] Backup storage is not publicly served.

## Frontend
- [ ] No backend credentials in frontend source.
- [ ] No secrets in production bundle.
- [ ] API base URL is deployment-configurable.
- [ ] Production errors do not display backend internals.

## Operations
- [ ] `.env` and secret files remain ignored.
- [ ] Production configuration is documented without real values.
- [ ] Backup/restore procedures are operator-controlled.
- [ ] Logs are reviewed for sensitive data.
- [ ] Dependencies are reviewed before production release.

## Final Gate
- [ ] Backend tests pass.
- [ ] Frontend lint/TypeScript/build pass.
- [ ] Production configuration checks pass.
- [ ] Manual verification completed by operator, if this phase is being declared fully production-verified.
