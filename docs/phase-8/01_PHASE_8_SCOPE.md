# Phase 8 — Income, Expense & Dashboard Analytics

## Objective
Implement shop income records, shop expense records, and a read-only dashboard that summarizes financial and operational data.

## In Scope
- Income records
- Expense records
- Controlled categories
- Date-range filtering
- Financial dashboard
- Operational dashboard
- OWNER/STAFF RBAC
- Audit trail
- Tests and regression verification

## Out of Scope
Customer billing/invoices, payment gateways, bank integrations, tax/PF/ESI, leave, notifications, WhatsApp/SMS, accounting ledger/double-entry bookkeeping, and changes to finalized payroll.

## Acceptance Criteria
- STAFF can create income and expense records.
- OWNER can read but cannot mutate them.
- Historical records are not physically deleted.
- Dashboard totals are derived from authoritative records.
- Date filters are inclusive.
- Existing Phase 1–7 functionality remains green.
