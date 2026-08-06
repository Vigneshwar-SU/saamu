# Phase 14 — Test Plan

## Authentication
- Anonymous report requests → 401.

## RBAC
- OWNER can read.
- STAFF can read.
- Reports cannot mutate records.

## Date Filters
Test no filter, date_from, date_to, date range, inclusive boundaries, invalid dates, and invalid/reversed ranges according to project conventions.

## Orders
Verify order counts, status breakdowns, and filtered results.

## Customers
Verify customer-related report values against database records.

## Tailors
Verify workload-related values against WorkAssignment data and existing authoritative calculations.

## Finance
Verify:
- income comes from customer payments
- refunds reduce income
- expenses come from Expense records
- net position is mathematically consistent
- report agrees with Phase 13 income summary and Phase 12 expense summary where applicable

## Regression
Protect billing, invoices, payments/refunds, expenses, income, payroll, settlement, orders, customers, tailors, and work assignments.

## Frontend Gates
- `npm run lint`
- `npx tsc --noEmit`
- `npm run build`

Do not weaken existing tests.
