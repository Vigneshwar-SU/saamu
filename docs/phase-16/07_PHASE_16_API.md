# Phase 16 — API Contract

An application API for backup/restore is optional and must only be introduced if the implementation genuinely benefits from it.

If introduced, it must follow `/api/v1/` conventions and:

- require authentication
- use explicit backup/restore permissions
- never accept arbitrary shell commands
- never accept arbitrary database credentials
- never expose secrets
- use fixed server-side backup locations
- validate backup identifiers
- use the standard error contract
- protect restore with explicit confirmation
- return operational status, not raw process internals
- reject unsupported methods

Suggested conceptual operations, only if justified by implementation:

- list available backups
- create backup
- validate backup
- restore selected backup

Do not expose a generic filesystem browser or shell endpoint.
