# Phase 21 — Production Deployment Runbook

This runbook prepares an operator for production deployment; it does not provision infrastructure.

## 1. Preflight
- Confirm a verified PostgreSQL backup exists.
- Confirm the backup is stored separately from source.
- Confirm secrets are supplied through the deployment environment.
- Confirm the target PostgreSQL instance is compatible.
- Confirm DNS/hostnames and HTTPS topology are known.
- Confirm rollback ownership and procedure.

## 2. Environment
Configure production values for:
- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- CORS settings if enabled
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`
- `DATABASE_HOST`
- `DATABASE_PORT`
- application/frontend API base URL
- static/media paths or storage settings

Never commit real values.

## 3. Build
- Install approved dependencies.
- Run backend checks.
- Run migrations only when explicitly authorized.
- Build frontend.
- Collect static assets according to deployment topology.

## 4. Start
Use a production WSGI/ASGI-capable application server appropriate to the selected infrastructure. Do not expose Django's development server publicly.

## 5. Smoke Test
Verify:
- health endpoint;
- login;
- OWNER/STAFF RBAC;
- customer/order workflows;
- reports;
- CSV/PDF export;
- WhatsApp-ready communication;
- reminders;
- database access.

## 6. Monitoring
Review application logs and server health. Ensure sensitive values are absent.

## 7. Rollback
If the deployment is unhealthy:
1. Stop public traffic.
2. Preserve logs.
3. Restore the previous application version/configuration.
4. Do not automatically restore the database unless the rollback plan explicitly requires it.
5. Use the Phase 16 verified backup/restore procedure for database recovery.
6. Smoke test before reopening traffic.
