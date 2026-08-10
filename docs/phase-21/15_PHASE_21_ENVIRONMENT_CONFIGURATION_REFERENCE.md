# Phase 21 — Environment Configuration Reference

This document is a reference, not a place to store real secrets.

## Classification

| Variable | Purpose | Development | Production | Secret |
|---|---|---|---|---|
| `DEBUG` | Django debug mode | `True` may be used locally | Must be `False` | No |
| `SECRET_KEY` | Django signing/security key | Local development value | Strong unique runtime secret | **Yes** |
| `ALLOWED_HOSTS` | Accepted HTTP hosts | Local host values | Explicit production hosts | No |
| `CSRF_TRUSTED_ORIGINS` | Trusted HTTPS origins | Usually local values | Explicit trusted origins | No |
| CORS origins | Allowed frontend origins | Local frontend | Exact production frontend origin(s) | No |
| `DATABASE_NAME` | PostgreSQL database | Existing local DB | Cloud/production DB | No |
| `DATABASE_USER` | PostgreSQL user | Existing local user | Production DB user | No |
| `DATABASE_PASSWORD` | PostgreSQL password | Local password | Production DB password | **Yes** |
| `DATABASE_HOST` | PostgreSQL host | `localhost` | Production DB hostname | No |
| `DATABASE_PORT` | PostgreSQL port | `5432` | Target PostgreSQL port | No |
| `BACKUP_DIR` | Operational backup storage | Local external folder | Secure operator-controlled location | No |
| `PG_BIN` | PostgreSQL CLI tools | Optional local path | Deployment-specific if required | No |
| Frontend API base URL | Backend API location | Local backend URL | Production API URL | No |

## Rules

### Secrets
Never:
- commit real values;
- put them in frontend code;
- print them in logs;
- return them from APIs;
- include them in screenshots/documentation.

### Development
Existing local PostgreSQL behavior should remain usable.

### Production
Production values must be explicitly configured. Missing or unsafe required values should fail validation before the application is treated as ready.

## File Boundaries

### Database Data
Handled by PostgreSQL and Phase 16 backup/restore.

### Media
Customer/order-uploaded files under the configured media storage.

### Static
Django static assets and frontend production build output.

### Backups
Stored outside the source tree and never served by Django.

### Logs
Operational diagnostics only; do not use logs as a substitute for database backups.

### Source
Application code and configuration templates, never real secrets.

## Pre-Deployment Review
- [ ] Every production variable has a known owner.
- [ ] Every secret has a secure injection mechanism.
- [ ] No real value appears in `.env.example`.
- [ ] Frontend bundle contains no private credentials.
- [ ] Database connectivity uses environment configuration.
- [ ] Backup location is separate from source.
- [ ] Static/media storage strategy is documented.
