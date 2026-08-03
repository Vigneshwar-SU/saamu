# Phase 7 — RBAC & Security

## OWNER
Read:
- advances
- payroll settlement
- payment history

Mutation attempts must return 403.

## STAFF
Can:
- create advances
- record payments
- apply eligible advances
- read settlement information

## Anonymous
Protected endpoints return 401.

## Financial Integrity
- Backend permissions are authoritative.
- Use transaction.atomic/select_for_update for payment/settlement mutations.
- Never trust client-provided outstanding values.
- Never allow negative balances.
- Never permit overpayment.
- Never modify finalized payroll earnings.
- No physical deletion of financial history.
