# Phase 16 — Requirements

## Functional requirements

### Backup
1. A STAFF/OWNER-safe operational workflow must be defined for creating database backups.
2. Backup files must use deterministic, timestamped naming.
3. Backup storage must be configurable and must not default to the application source tree when a safer location is available.
4. A backup must not be reported as successful unless the command/process completed successfully and the resulting file is usable.
5. Backup metadata/status must clearly distinguish successful, failed, and unavailable operations.

### Restore
1. Restore must be treated as a destructive operation.
2. The system must require an explicit confirmation/safety mechanism before restoring.
3. A fresh pre-restore backup must be created before replacing the live database whenever technically applicable.
4. Restore must never silently overwrite the live database.
5. Failed restores must surface a clear failure state.
6. Restore verification must confirm that the database is reachable and structurally usable after restoration.
7. The workflow must document what happens to data created after the selected backup.

### Portability
1. PostgreSQL must remain the authoritative business-data store.
2. The backup format must support restoration to another PostgreSQL instance.
3. The workflow must document local → cloud database migration without requiring application-level data conversion.
4. Database backups must be explicitly distinguished from media/uploads, static files, environment secrets, logs, and application source/build artifacts.

### Safety
- Never expose database credentials to the frontend.
- Never allow an ordinary API request to trigger an unrestricted destructive shell command.
- Never accept arbitrary filesystem paths or arbitrary commands from the client.
- Never let OWNER/STAFF RBAC be bypassed by frontend controls.
- Do not delete existing production data as part of normal backup operations.

## Architectural constraint
Prefer an operator-controlled local management workflow over exposing destructive database administration through the browser. If an in-app workflow is introduced, it must be tightly constrained, audited, and backend-authoritative.
