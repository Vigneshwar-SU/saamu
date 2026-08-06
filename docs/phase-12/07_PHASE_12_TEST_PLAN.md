# Phase 12 — Test Plan

## Backend Gates
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest apps/expenses
python -m pytest
python -m black --check apps
python -m isort --check-only apps
```

## Required Tests
- Valid creation
- Missing/invalid required fields
- Zero/negative amounts
- Decimal integrity
- Category/payment/date filters
- Date-range filtering
- Summary correctness
- `recorded_by` cannot be spoofed
- Anonymous/OWNER/STAFF RBAC
- Frontend lint, TypeScript and build

## Regression
Phase 11 baseline is 456 passing backend tests. Phase 12 must not regress existing functionality.

Automated tests do not count as manual verification.
