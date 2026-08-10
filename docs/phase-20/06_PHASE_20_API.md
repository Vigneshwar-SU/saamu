# Phase 20 — API Specification

## Default
No new application API is required for cloud migration.

Phase 16 deliberately avoided browser-facing database administration because destructive database operations must remain explicit operator procedures.

## Optional Readiness Endpoint
An endpoint may be introduced only if repository inspection establishes a genuine operational need and the implementation can remain safe.

If introduced:
- GET/read-only only.
- Follow existing authentication/security conventions.
- Never return credentials, connection strings, filesystem paths, or sensitive database internals.
- Never run migrations, backups, restores, shell commands, or provider operations.
- Use the existing standard success/error envelope.
- Add appropriate authorization tests.

Do not invent an API solely to increase Phase 20 scope.
