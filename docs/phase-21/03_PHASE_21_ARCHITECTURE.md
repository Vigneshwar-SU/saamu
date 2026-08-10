# Phase 21 — Architecture

## Principle
Phase 21 is an application-hardening phase. It prepares Django and the frontend for deployment while keeping infrastructure provider-neutral.

## Configuration Layers
- Development: existing local defaults remain usable.
- Production: environment variables explicitly define security-sensitive settings.
- Secrets: supplied only through environment/runtime secret management.
- Frontend: only public configuration may be exposed to the browser.

## Security Boundaries
- Django application
- PostgreSQL database
- Media/uploads
- Static/frontend build
- Backup storage
- Logs
- Secrets

These must not be treated as one deployable data blob.

## Error Boundary
Production responses must expose safe error information only. Detailed diagnostics belong in controlled server logs, without credentials, tokens, passwords, or connection strings.

## Deployment Boundary
The phase may add deployment documentation/configuration templates, but must not provision infrastructure or perform a live migration.
