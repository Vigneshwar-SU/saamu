# Phase 16 — Frontend

If a UI is required by the approved implementation, keep it deliberately operational rather than decorative.

## Backup UI requirements
- Show backup status clearly.
- Show available backup metadata without exposing secrets.
- Provide explicit confirmation before destructive restore actions.
- Make destructive actions visually distinct.
- Disable duplicate actions while a backup/restore operation is pending.
- Clearly distinguish backup creation from restore.
- Clearly surface success, failure, unavailable tooling, and validation errors.
- Do not expose raw server paths, credentials, or shell commands unnecessarily.

## React Query
Use the existing service/hook/query-key architecture.

Invalidate or refresh backup metadata only when an operation actually changes it.

## Important
A browser UI must never become a generic shell or database administration console.
