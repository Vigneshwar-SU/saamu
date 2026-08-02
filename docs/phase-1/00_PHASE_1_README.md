# Saamu Tailors — Phase 1 README

## Purpose
Phase 1 establishes the technical foundation of Saamu Tailors before business features are implemented.

Phase 0 is the source of truth for product vision, workflow, Version 1 scope, roles, business rules, architecture, domain model, API architecture, and non-functional requirements.

## Scope
- Repository/project structure
- One Python virtual environment
- PostgreSQL-only configuration
- Django + DRF foundation
- Environment configuration
- `/api/v1/` API versioning
- Secure default API permissions
- JWT foundation readiness
- CORS
- Standard API errors
- Pagination defaults
- Logging foundation
- Health endpoint
- Static/media configuration
- React/TypeScript/Vite foundation
- Centralized API client
- Frontend error handling foundation
- Testing foundation
- Git/.gitignore
- README/setup documentation

## Out of Scope
No customer, measurement, order, garment, tailor, workload, salary, payment, income, expense, locker, collection, bill, WhatsApp/SMS, dashboard, report, business notification, or OWNER/STAFF business-authorization functionality.

## Principles
1. PostgreSQL only; no SQLite fallback.
2. Environment-driven configuration.
3. APIs under `/api/v1/`.
4. Backend validation is authoritative.
5. Never hard-code secrets or URLs.
6. Keep the local-first design simple and cloud-migration friendly.
7. Do not invent business rules.
8. Do not proceed automatically to Phase 2.
