# Phase 16 — Architecture

## Existing baseline
- Django + Django REST Framework
- PostgreSQL-only
- React + TypeScript
- React Query
- JWT authentication
- OWNER / STAFF RBAC
- Local Windows deployment
- Phase 15 documented pg_dump/pg_restore procedure

## Design principles

### PostgreSQL remains authoritative
Do not create a second application database or JSON-based business-data backup format.

### Backup format
Prefer PostgreSQL's native backup tooling (`pg_dump`, preferably custom format where appropriate) so backups remain portable to another PostgreSQL instance.

### Application vs database
Keep these concepts separate:
- PostgreSQL data/schema
- media/uploads
- frontend build/static files
- backend source code
- `.env` and secrets
- logs
- backup artifacts

### Destructive operations
Restore must be explicitly protected. Do not provide a generic command-execution endpoint.

### Local-first, cloud-ready
The design should work on the current Windows/local PostgreSQL installation and should not hard-code assumptions that prevent a future hosted PostgreSQL database.

### Auditability
Where the application exposes backup/restore actions, record enough operational information to identify when an action occurred, its result, and the responsible authenticated operator without storing secrets.

### No unnecessary migration
A schema migration is not expected for this phase. Introduce one only if implementation proves it is genuinely required.
