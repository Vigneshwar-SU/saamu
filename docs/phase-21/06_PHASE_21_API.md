# Phase 21 — API Specification

## Existing APIs
No existing business endpoint should change its response contract unless a concrete security defect requires it.

## Health
Review the existing `GET /api/v1/health/` endpoint.

It must remain:
- safe for its intended public/readiness role;
- free of secrets;
- free of database credentials;
- free of filesystem paths;
- free of executable commands;
- useful for determining application/database readiness.

## Error Contract
Preserve the existing standard error envelope.

Production errors must not expose:
- Django tracebacks;
- SQL credentials;
- environment variables;
- filesystem internals;
- secret keys.

## New Endpoints
None are required by default.

Do not add browser-facing deployment, shell, backup/restore, migration, or infrastructure-control endpoints.
