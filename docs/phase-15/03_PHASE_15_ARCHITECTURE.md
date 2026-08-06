# Phase 15 — Architecture & Guardrails

## Principles
- Harden the existing architecture; do not create duplicate systems.
- Keep Django/DRF as the source of truth.
- Keep PostgreSQL as the authoritative local database.
- Keep React Query cache invalidation aligned with mutations.
- Reuse existing services for financial/report calculations.
- Preserve the existing RBAC model.
- Prefer small, isolated changes over rewrites.

## Areas to Review
- Authentication and authorization.
- API validation and error handling.
- Query efficiency and N+1 risks.
- React Query stale/cache behavior.
- Global frontend error states.
- Database backup/restore.
- Environment/configuration safety.
- Logging and operational diagnostics.
