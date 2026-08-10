# Phase 20 — Backend Specification

## Objective
Harden backend configuration for portability while preserving local operation.

## Required Work
1. Inspect config/settings.py and the existing .env.example.
2. Identify current database configuration and make it environment-driven where needed.
3. Preserve the existing local PostgreSQL setup.
4. Add explicit production configuration validation for missing/unsafe required settings where justified by the existing settings architecture.
5. Ensure secret values never appear in validation errors, logs, or exception text.
6. Remove/avoid hard-coded local-only assumptions from runtime configuration.
7. Ensure backup paths remain operationally separate from source code.
8. Add a safe health/readiness mechanism only if justified by the existing architecture; do not create a destructive administration endpoint.
9. Do not change business models or serializers.

## Cloud Compatibility
The backend should connect to a compatible PostgreSQL instance using environment-provided host, port, database, user, and password.

SSL or provider-specific options may be supported only through generic configuration; do not hard-code one cloud vendor.

## Error Handling
Configuration failures should identify the missing/invalid category, avoid credentials, and fail before an unsafe production start where appropriate.

## Database
No migration is expected. Run makemigrations --check --dry-run.
