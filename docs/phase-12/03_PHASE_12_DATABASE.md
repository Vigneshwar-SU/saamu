# Phase 12 — Database Specification

## Expense Model
Minimum fields:
- id
- category
- amount
- expense_date
- description
- payment_method
- recorded_by
- created_at
- updated_at

Use existing project base/time-stamped conventions.

## Amount
Decimal, greater than zero, never floating-point storage.

## recorded_by
Foreign key to authenticated user. Client cannot assign it.

## Category / Payment Method
Use controlled choices. Final values must be defined before implementation.

## Indexing
Consider indexes for expense_date, category, payment_method and recorded_by only where justified.

## Migration
Run:
`python manage.py makemigrations --check --dry-run`
and ensure no pending changes after implementation.

## Integrity
Enforce amount > 0 and valid foreign keys/controlled values where possible.
