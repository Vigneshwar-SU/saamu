# Phase 15 — Backend Hardening

## Tasks
- Review protected endpoints for authentication and RBAC consistency.
- Review serializer validation and standard API error responses.
- Review list/detail endpoints for unnecessary queries.
- Add select_related/prefetch_related only where justified.
- Review pagination and filter validation.
- Verify financial services remain server-side authoritative.
- Verify read-only endpoints reject mutations with 405.
- Review exception handling and avoid leaking sensitive implementation details.
- Review production settings for DEBUG, allowed hosts, secrets and database configuration.
- Add targeted regression tests only where a real gap is found.

## Guardrail
Do not modify business behavior merely for cleanup. Any behavior change must be explicitly justified and tested.
