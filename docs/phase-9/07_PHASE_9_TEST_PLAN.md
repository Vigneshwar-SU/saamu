# Phase 9 — Test Plan

## Backend Baseline
Run before implementation:
- `python manage.py check`
- `python manage.py migrate --check`
- Full existing pytest suite.

## Invoice Tests
- Anonymous 401.
- OWNER list/detail succeeds.
- OWNER create rejected with 403.
- STAFF create succeeds.
- Duplicate order invoice rejected.
- Invoice number unique.
- Invoice item snapshots correct.
- Correct subtotal/total.
- Invalid order rejected.
- Historical invoice remains unchanged after order edits.

## Payment Tests
- OWNER payment history read succeeds.
- OWNER payment mutation rejected.
- STAFF payment succeeds.
- Zero/negative payment rejected.
- Overpayment rejected.
- Exact final payment produces PAID.
- Multiple partial payments produce PARTIALLY_PAID.
- No payment produces UNPAID.
- Payment history append-only.
- `recorded_by` server-authoritative.

## Date/Filter Tests
- Inclusive date boundaries.
- Reversed date range rejected.
- Invalid date rejected.
- Pagination works.
- Status/method filters work.

## Concurrency
Two simultaneous payment attempts must never create an overpayment. Use a transactional test with row locking.

## Regression
All Phase 1–8 tests must remain green.

## Frontend
```text
npm run lint
npx tsc --noEmit
npm run build
```
