# Phase 21 — Scope

## Title
Production Hardening & Deployment Readiness

## Objective
Harden Saamu Tailors for a future production/cloud deployment without performing the actual cloud migration.

## In Scope
- Django production security settings and validation.
- CSRF/CORS/allowed-host configuration review.
- Secure cookies and HTTPS/security-header configuration.
- Static/media deployment boundaries.
- Production-safe logging and error handling.
- Health/readiness behavior review.
- Secure environment configuration.
- Application server/runtime deployment guidance.
- Production smoke-test and rollback preparation.
- Regression tests and documentation.
- Security-hardening checklist.
- Environment configuration reference.

## Out of Scope
- Actual cloud provider selection or provisioning.
- Live database migration.
- Cloud object storage/CDN implementation.
- Automated cloud backups.
- Automatic WhatsApp/SMS/email sending.
- Payment gateways, GST, accounting integrations.
- New business modules.
- UI redesign.
- Browser-based database administration.

## Core Rule
Do not invent infrastructure or introduce provider-specific dependencies unless the repository and requirements justify them.
