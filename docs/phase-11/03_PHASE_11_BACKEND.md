# Phase 11 — Backend Implementation Specification

## Backend
Use the existing Django + Django REST Framework architecture.

## Rules
1. Inspect the current payment, order, customer, tailor, and payroll implementations before changing anything.
2. Reuse existing models/services where appropriate.
3. Do not duplicate Phase 7 settlement logic.
4. Keep financial calculations authoritative on the backend.
5. Create Django migrations for schema changes.
6. PostgreSQL remains the only database.
7. Preserve existing API error conventions.
8. Enforce permissions server-side.

## Expected Backend Areas
Depending on the existing repository structure, Phase 11 may require changes to:
- payment/order models
- serializers
- views/viewsets
- services
- URLs
- permissions
- admin
- tests
- migrations

Do not create files merely because they are listed here. Modify the existing architecture based on repository inspection.

## Data Integrity
- Payment totals must be calculated from persisted transactions.
- Refunds must remain auditable.
- Historical payment records must not be silently destroyed.
- Existing finalized payroll data must remain immutable.
