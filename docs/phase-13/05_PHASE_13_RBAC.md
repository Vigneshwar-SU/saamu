# Phase 13 — RBAC and Security

Backend authorization remains authoritative.

## Anonymous
Income list/summary → `401 Unauthorized`.

## OWNER
Can:
- View income.
- View summaries.
- Filter income.
- View dashboard income.

Cannot mutate customer payments/refunds through Income Management.

## STAFF
Can:
- View income.
- View summaries.
- Filter income.

Payment/refund mutations remain controlled by existing Phase 11 billing permissions.

## Security
Never accept client-supplied authoritative:
- total_income
- net_income
- recorded_by
- payment amount

Income viewing must not bypass existing billing permissions.
