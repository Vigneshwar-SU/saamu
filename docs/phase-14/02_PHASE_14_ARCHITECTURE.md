# Phase 14 — Architecture

Phase 14 is a read-only reporting layer over existing modules.

## Authoritative Sources
Use existing data from:
- Orders
- Customers
- Tailors / WorkAssignments
- Payroll / settlements where applicable
- CustomerPayment / refunds
- Expenses
- Existing finance/dashboard services

Do not duplicate financial or operational records.

## Architecture
Database records → reusable backend reporting services → reporting API → React Query services/hooks → Reports UI.

All authoritative aggregation must happen server-side.

## Reuse
Reuse existing calculation services whenever they already provide the correct business meaning. Avoid implementing the same calculation separately in API views, dashboard, frontend, or individual cards.

## RBAC
Reporting is read-only. Existing backend authorization remains authoritative.
