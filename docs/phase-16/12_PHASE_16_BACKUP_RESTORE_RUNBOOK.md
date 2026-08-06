# Phase 16 — Backup & Restore Runbook

Status: **IMPLEMENTED** (tooling added and automatically tested). Live
backup/restore against real shop data is an operator action and remains under
manual verification (see `08_PHASE_16_MANUAL_VERIFICATION.md`, still
**NOT STARTED**).

## 1. Purpose

Operational procedure for protecting and recovering Saamu Tailors PostgreSQL
data using the PostgreSQL-native tooling shipped in Phase 16:

| Command | Purpose |
|---|---|
| `python manage.py db_backup` | Create a timestamped custom-format backup |
| `python manage.py db_list_backups` | List backups in the configured location |
| `python manage.py db_verify [--restore-test]` | Verify a backup (and optionally test-restore it) |
| `python manage.py db_restore` | Restore a known backup (destructive, guarded) |
| `python manage.py db_cleanup` | Enforce retention (dry-run by default) |

All commands run on the local Windows deployment from the `backend` directory
with the virtual environment activated:

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py <command>
```

## 2. Configuration

Everything is driven by `backend/.env` (loaded automatically by Django). No
credentials are ever embedded in scripts, filenames, or committed files.

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_NAME` / `DATABASE_USER` / `DATABASE_PASSWORD` / `DATABASE_HOST` / `DATABASE_PORT` | PostgreSQL connection (existing) | `saamu_db` / `postgres` / `localhost` / `5432` |
| `BACKUP_DIR` | Backup storage location, **outside the source tree** | `%USERPROFILE%\SaamuBackups` |
| `PGBIN` | Directory containing `pg_dump` / `pg_restore` / `psql` | empty (tools located on `PATH`) |

Example for the documented local PostgreSQL 18 install:

```dotenv
BACKUP_DIR=D:\SaamuBackups
PGBIN=C:\Program Files\PostgreSQL\18\bin
```

Safety rules:

- Never point `BACKUP_DIR` inside the repository (`D:\Projects\saamu\...`).
- Never commit `backend/.env`; it is git-ignored.
- The database password is passed to the child process only through the
  `PGPASSWORD` environment variable and is never printed, logged, or embedded
  in backup filenames.

## 3. Before backup

- Confirm PostgreSQL is reachable (`python manage.py check`).
- Confirm the backup destination exists and has sufficient disk space
  (`python manage.py db_list_backups` creates/reads `BACKUP_DIR`).
- Confirm `BACKUP_DIR` is outside the application source tree.
- Confirm credentials are supplied through `backend/.env` and are not written
  into scripts or shell history.

## 4. Backup

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py db_backup
```

What happens:

1. `pg_dump` runs against the configured database with `--format=custom
   --no-owner --no-privileges`, producing a compressed, selectively-restorable,
   portable archive.
2. The file is written to `BACKUP_DIR` with a deterministic, timestamped name:
   `saamu_db_YYYY-MM-DD_HHMMSS.dump`.
3. An existing file with the same name is never overwritten (the command fails
   and asks you to retry).
4. By default the artifact is verified before success is reported: the file
   exists, is non-empty, and `pg_restore --list` can read its catalog. A
   backup is only reported successful when the process succeeded **and** the
   file is usable.

Optional flags:

```powershell
python manage.py db_backup --comment "weekly manual backup"
python manage.py db_backup --no-verify   # not recommended
```

Record after every backup:

- timestamp and backup filename,
- database/environment backed up (e.g. `saamu_db` on `localhost`),
- success/failure,
- verification result.

## 5. Backup verification

A successful `pg_dump` alone is not proof of recoverability.

### 5.1 Quick verification

```powershell
python manage.py db_verify --backup saamu_db_2026-08-06_120000.dump
# or, to verify the newest backup:
python manage.py db_verify
```

Checks performed:

- the file exists,
- the file is non-empty,
- PostgreSQL tooling can inspect/read it (`pg_restore --list` succeeds and the
  archive has catalog entries),
- the archive format is PostgreSQL custom format.

### 5.2 Restore test (recommended before trusting a backup)

The strongest proof of recoverability is a real restore into a disposable
database. This is the **only** restore practice allowed:

```powershell
python manage.py db_verify --restore-test
```

This performs the documented safe workflow:

```
backup → disposable restore database (saamu_restore_test)
      → restore → compare representative row counts against the source
      → run integrity checks → drop the disposable database
```

Never test a destructive restore against the live shop database.

## 6. Backup retention

Naming is chronological (`saamu_db_YYYY-MM-DD_HHMMSS.dump`), so newest-first
ordering is deterministic.

Recommendation:

- keep daily backups for the current week,
- keep at least one backup from a previous month,
- never keep a single "only copy".

Enforce retention with the cleanup command. It is a **dry-run by default** and
only ever considers files that match the strict backup naming convention:

```powershell
python manage.py db_cleanup --keep 10            # show what would be removed
python manage.py db_cleanup --keep 10 --execute  # actually remove expired
```

Deletion is explicit and operator-triggered; nothing is deleted automatically.
Do not delete the only known-good backup before a replacement is verified.

## 7. Restore safety

Restore is a **destructive operation** and is treated as an explicit operator
procedure, not an application mutation. The tool refuses to run without
confirmation.

### 7.1 Live restore procedure (only after a verified backup)

1. **Stop or restrict application writes.** Bring down the Django backend that
   writes to the database (the restore is blocked while the target has active
   connections; pass `--force` only when you are certain nothing is writing).
2. **Create a fresh pre-restore safety backup.** The tool does this
   automatically and prints the safety backup filename. Preserve it until the
   restore is confirmed. If the current database is already broken, pass
   `--skip-safety-backup` — do not skip otherwise.
3. **Confirm the intended target database.** The tool prints the target,
   host, port and user before you confirm.
4. **Restore only the selected known backup.** The backup name is validated
   server-side; arbitrary paths are rejected.
5. **Run integrity checks.** The tool verifies the restored database is
   reachable, has tables, has Django migrations recorded, and reports
   representative record counts.
6. **Re-enable application access.**
7. **Verify critical business records** (customers, orders, payments,
   expenses, payroll) before relying on the restored database.

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py db_list_backups
python manage.py db_restore --backup saamu_db_2026-08-06_120000.dump
# interactive mode: type RESTORE when prompted
# or, for a non-interactive run where you have already confirmed intent:
python manage.py db_restore --backup saamu_db_2026-08-06_120000.dump --yes
```

The confirmation prompt states exactly which backup and which target database
will be affected. Without `--yes` and without a live terminal, the command
aborts with a clear error — it never silently restores.

### 7.2 What happens to data created after the selected backup

The database is replaced with the state captured in the backup. Any records
created after the backup's timestamp are lost. This is why a fresh
pre-restore safety backup is taken first: it captures the "current" state so
that data created after the selected backup is recoverable from the safety
backup.

## 8. What a PostgreSQL backup does and does not contain

### Included (custom-format dump)

- Every table in the `saamu_db` database: schema (tables, indexes,
  constraints, sequences) and all rows.
- Users, RBAC roles, audit fields and all financial history.
- Sequences, so invoice/order numbers continue correctly after a restore.

### NOT included

A PostgreSQL dump does **not** automatically contain:

- **Uploaded media files** under `backend/media/` — currently unused by
  Version 1 features; if media is ever added it must be backed up separately.
- **Generated/static build output** (`backend/static/`, `frontend/dist/`) —
  regenerated by `collectstatic` / `npm run build`.
- **`.env` and secrets** (`SECRET_KEY`, database password, external-service
  credentials) — stored and backed up separately, never inside the dump.
- **Logs** (`backend/logs/`).
- **Application source code** and frontend build artifacts.
- **Machine-specific configuration** (paths, `PGBIN`, `ALLOWED_HOSTS`,
  CORS origins).

There is no "complete backup" command that captures all of the above; the
database backup covers the database only. Treat each category as its own
backup concern.

## 9. Never

- test a destructive restore against the live database,
- overwrite the only known-good backup,
- paste credentials into shell history or source code,
- restore a backup that has not been verified,
- report a backup as successful when verification failed,
- skip the pre-restore safety backup unless the current database is already
  broken or empty.

## 10. Recovery failure

If a restore fails or the restored database does not pass verification:

- Do **not** claim recovery success.
- Preserve:
  - the pre-restore safety backup,
  - the original backup,
  - the logs needed to diagnose the issue (`backend/logs/saamu.log`).
- Diagnose the failure, fix the cause, and restore again following section 7.
- Only consider recovery complete after post-restore verification passes and
  representative business records are confirmed.

## 11. Manual verification

The operator checklist in
`docs/phase-16/08_PHASE_16_MANUAL_VERIFICATION.md` is the authoritative record
of real, manually-performed backup/restore against shop data. It remains
**NOT STARTED**; automated tests do not count as manual verification.
