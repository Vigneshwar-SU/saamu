# Phase 16 — Backup, Restore & Data Portability

## Status
Planning

## Objective
Make the local Saamu Tailors installation operationally safe by providing a controlled backup/restore workflow and a clear data-portability foundation for the eventual local-to-cloud transition.

This phase builds on the PostgreSQL backup/restore procedure documented in Phase 15 and turns the operational procedure into a robust, application-aware capability where safe and justified.

## Core goals
- Reliable PostgreSQL backup creation.
- Safe backup discovery and validation.
- Controlled restore workflow with explicit safeguards.
- Pre-restore safety backup.
- Restore verification and integrity checks.
- Clear operator-facing status and failure handling.
- Configurable local backup storage.
- Retention/cleanup strategy without deleting the live database.
- Clear separation of database data, media/uploads, static/build files, environment secrets, and source code.
- Documented migration path from local PostgreSQL to a future hosted PostgreSQL environment.
- No duplicate business-data store.

## Non-goals
Exports, WhatsApp/SMS communication, cloud deployment, payment gateways, GST, double-entry accounting, and unrelated business features are deferred to later phases.
