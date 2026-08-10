# Phase 20 — Scope

## Title
Cloud Migration Readiness & Deployment Foundation

## Purpose
Prepare Saamu Tailors to move from the current local Windows/PostgreSQL installation to a cloud-hosted PostgreSQL deployment without changing business behavior.

Phase 16 already provides PostgreSQL-native custom-format backup/restore and documents a local → cloud migration path. This phase turns that documented path into a controlled application/deployment foundation.

## In Scope
- Environment-driven PostgreSQL configuration suitable for local and cloud targets.
- Production-safe configuration validation.
- Explicit separation of database data, media/uploads, static/build assets, secrets, source code, and backups.
- Cloud migration readiness documentation and operator checklist.
- Safe pre-migration validation and post-migration smoke checks.
- Deployment configuration that does not hard-code local machine assumptions.
- Tests for configuration and migration-readiness behavior.
- README/project documentation updates.

## Explicitly Out of Scope
- Choosing or purchasing a cloud provider.
- Creating a paid cloud account or provisioning infrastructure.
- Executing a live production migration.
- Automatically uploading backups to cloud storage.
- Managed backup scheduling.
- CDN/object-storage integration.
- Automatic WhatsApp/SMS sending.
- New business modules.
- Database schema redesign.
- UI redesign.
- Payment gateways, GST, double-entry accounting.

## Safety Principle
The local installation remains the source of truth until a human operator completes a controlled migration and verifies the cloud deployment. Never delete or overwrite the local database merely because a cloud target is configured.
