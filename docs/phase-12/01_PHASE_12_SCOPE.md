# Phase 12 — Expense Management

## Objective
Implement a complete expense management module for Saamu Tailors.

## In Scope
- Create, view, filter and manage expenses.
- Category, amount, date, description, payment method and recorded user.
- Expense summaries: total, category totals, date/period totals and count.
- OWNER: read-only.
- STAFF: management access.
- Backend-authoritative financial calculations and permissions.

## Out of Scope
Customer payments, refunds, invoices, digital bills, payment gateways, GST automation, double-entry accounting, automatic income creation, payroll changes, salary settlement changes, WhatsApp/SMS, bank/cloud accounting integration.

## Financial Rules
- Amount must be greater than zero.
- Totals are calculated server-side.
- `recorded_by` comes from the authenticated user.
- Financial values use Decimal.
- Summaries are derived from expense records.

## Regression Guardrails
Do not break Orders, Customers, Tailors, Work Assignments, Payroll, Invoices, Payments, Refunds or Digital Bills.

Phase 11 baseline: 456 backend tests passing.

## Completion Criteria
Implement database, API, RBAC, frontend, summaries, validation and automated tests; pass backend/frontend quality gates; update documentation and write a completion report. Manual verification must be separately recorded.
