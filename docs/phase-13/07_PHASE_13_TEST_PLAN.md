# Phase 13 — Test Plan

## Authentication
- Anonymous income list → 401.
- Anonymous income summary → 401.

## RBAC
- OWNER can read.
- STAFF can read.
- Income view has no payment mutation capability.

## Income
- Real customer payment increases income exactly once.
- Multiple payments aggregate correctly.

## Refunds
Verify:
- payment increases net income.
- partial refund decreases net income.
- full refund can reduce the contribution to zero.
- refunds are never counted as positive income.

## Filters
Test:
- date_from
- date_to
- date range
- payment method
- payment type where supported
- combined filters

## Summary
Verify API totals equal database-derived payment aggregation.

## Dashboard
Verify dashboard income and Income summary use the same calculation.

## Regression
Run the full backend suite and ensure Phase 11 billing, Phase 12 expenses, Phase 7 payroll/settlement, orders, customers, tailors and other modules remain green.

## Frontend Gates
- `npm run lint`
- `npx tsc --noEmit`
- `npm run build`

Do not weaken existing tests.
