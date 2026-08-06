# Phase 16 — Local to Cloud PostgreSQL Migration

Status: **DOCUMENTED** (procedure only). No cloud deployment or cloud database
was created as part of Phase 16. Cloud hosting is explicitly outside this
phase; this document is the portability blueprint.

## 1. Goal

Move Saamu Tailors from the current local PostgreSQL installation to a future
hosted PostgreSQL instance **without changing business-data semantics**.

The Django application keeps using the same database abstraction and models —
only the connection settings change. No application-level data conversion is
needed because backups are produced with PostgreSQL-native tooling
(`pg_dump` custom format) which restores into any compatible PostgreSQL.

## 2. Current local architecture

```text
React frontend → Django REST API → PostgreSQL (local, saamu_db)
```

## 3. Target architecture

```text
React frontend → Django REST API → Hosted PostgreSQL (cloud, e.g. saamu_db)
```

## 4. What is and is not migrated by the database

A PostgreSQL dump (`saamu_db_YYYY-MM-DD_HHMMSS.dump`) contains the database
only. It does **not** migrate these, which require separate procedures:

| Category | Example | Migrated by dump? |
|---|---|---|
| Database data | customers, orders, payments, expenses, payroll, users, sequences | Yes |
| Media / uploads | `backend/media/` (currently unused by Version 1) | No — copy separately |
| Static / build output | `backend/static/`, `frontend/dist/` | No — regenerate (`collectstatic` / `npm run build`) |
| Environment secrets | `backend/.env` (`SECRET_KEY`, DB password) | No — recreate on target, never copy into the dump |
| Logs | `backend/logs/` | No |
| Application source code | the `saamu` repository | No — deploy from the repository |
| External-service credentials | payment/notification keys (future phases) | No — store in the target environment |

Explicitly: `pg_dump` does not automatically back up media, static files,
secrets, logs, or source code. Do not rely on the database dump for any of
these.

## 5. Migration outline

### 5.1 Freeze or minimize writes

Stop business activity or place the shop on a read-only footing so the final
backup is internally consistent.

### 5.2 Create and verify a fresh backup

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py db_backup
python manage.py db_verify --restore-test   # prove the backup is restorable
```

Record the backup filename and its verification result.

### 5.3 Provision the target PostgreSQL database

Create the target database on the hosted PostgreSQL service (name, e.g.
`saamu_db`), plus a role with rights matching what Django needs
(`DATABASE_USER`).

### 5.4 Apply compatible database configuration / environment variables

Create the cloud `backend/.env` (or cloud secret store) with:

```dotenv
DATABASE_NAME=saamu_db
DATABASE_USER=<cloud user>
DATABASE_PASSWORD=<cloud password>   # never committed
DATABASE_HOST=<cloud host>
DATABASE_PORT=5432
```

Do **not** copy `SECRET_KEY` or other secrets into the database dump.

### 5.5 Restore the backup into the target

Transfer the backup file securely (scp/cloud object storage with access
controls), then restore. Locally this can be validated first:

```powershell
# optional: practice against a local disposable database
python manage.py db_verify --restore-test
```

The documented manual procedure against the target database uses PostgreSQL
tooling directly:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" `
  --host <cloud host> --port 5432 --username <cloud user> `
  --dbname saamu_db --no-owner --no-privileges --clean --if-exists `
  "D:\SaamuBackups\saamu_db_YYYY-MM-DD_HHMMSS.dump"
```

Credentials for the cloud restore come from the environment
(`PGPASSWORD`/`pgpass`); never embed them in commands you commit or share.

### 5.6 Run schema / application checks

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py check
python manage.py showmigrations   # confirm all migrations are applied
python manage.py migrate --check  # fails if any migration is unapplied
```

### 5.7 Verify representative business records

Confirm expected rows exist and relationships hold for:

- users (authentication) and RBAC roles
- customers
- orders and order items
- invoices and invoice items
- customer payments / refunds
- expenses
- payroll periods, payroll entries and salary advances

### 5.8 Point the application at the target database

Update the cloud `DATABASE_*` variables (step 5.4) and restart the backend.
Run the health check:

```text
GET /api/v1/health/   →   { "status": "ok", "database": "ok" }
```

### 5.9 Run smoke tests

Confirm login, orders, customers, tailors, attendance, payroll, payments,
income, expenses, invoices, reports and the dashboard all read correctly from
the cloud database.

### 5.10 Keep the original until proven stable

Keep the original local database and the pre-migration backup until the cloud
environment has been stable for a reasonable period. Never delete the only
known-good copy before the replacement is verified.

## 6. Environment-variable portability notes

The Django settings already read everything from environment variables:

- `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`,
  `DATABASE_PORT` — database connection.
- `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` — target-host allow-listing.
- `SECRET_KEY`, `DEBUG` — security posture of the target deployment.
- `STATIC_ROOT`, `MEDIA_ROOT`, `LOG_DIR` — path overrides for the target.

The Phase 16 backup tooling (`BACKUP_DIR`, `PGBIN`) is local-only; the cloud
deployment does not need it for normal operation.

## 7. What must NOT be copied into the database dump

- `.env` values (secrets) — never written into the dump by `pg_dump`.
- Passwords or connection strings in filenames, logs, or scripts.

## 8. What must be migrated separately

- media/uploads (if any are introduced later),
- static files / build output,
- `.env` and secrets,
- logs,
- application source code (deploy from the repository),
- monitoring/backup scheduling for the cloud database.

## 9. Future cloud phase

Cloud storage, automated backups, deployment, HTTPS, monitoring and production
hosting are explicitly outside Phase 16. This document only guarantees the
data-portability path.
