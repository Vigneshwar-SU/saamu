# Phase 16 — Deferred Items & Guardrails

## Deferred
- Cloud-hosted backup storage
- Automated cloud backup
- Cloud deployment
- WhatsApp/SMS
- Report export/PDF/Excel
- Payment gateways
- GST automation
- Double-entry accounting
- Bank/cloud accounting integration
- Scheduled business reminders
- Unrelated UI redesign

These are candidates for later phases.

## Guardrails

### Never
- execute arbitrary client-supplied shell commands
- accept arbitrary database credentials from users
- expose `.env`, `SECRET_KEY`, DB passwords, or connection strings
- restore directly over the live database without explicit safety controls
- delete the only available backup before confirming a replacement is valid
- assume a successful process exit alone proves business-data recoverability
- claim a backup is cloud-ready without a tested PostgreSQL portability path

### Preserve
- PostgreSQL-only architecture
- backend-authoritative RBAC
- standard error contract
- Phase 13 derived income
- Phase 14 reports
- Phase 15 hardening
- existing uncommitted work from prior phases
