# Phase 21 — Backend Specification

## Goals
Harden Django settings without changing business behavior.

## Required Review
Inspect:
- DEBUG
- SECRET_KEY
- ALLOWED_HOSTS
- CSRF_TRUSTED_ORIGINS
- CORS policy
- secure cookies
- HTTPS/security headers
- session configuration
- database configuration
- logging
- error handling
- static/media settings
- health endpoint
- environment loading

## Production Validation
Production startup/checks should fail fast for unsafe required configuration while development remains convenient.

Validation errors must:
- be deterministic;
- identify configuration categories;
- never print actual secret values;
- never print full database configuration.

## Logging
Logs should be useful for operational diagnosis while excluding:
- passwords;
- tokens;
- authorization headers;
- cookies;
- full customer phone numbers where avoidable;
- database connection strings.

## Database
Use the existing environment-driven PostgreSQL configuration. Do not introduce provider-specific database code.

## No Business Changes
Orders, customers, measurements, tailors, payroll, payments, reports, communications, reminders and backup/restore behavior must not change.
