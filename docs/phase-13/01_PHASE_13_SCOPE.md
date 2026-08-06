# Phase 13 — Income Management: Scope

## Objective
Implement Income Management for Saamu Tailors using actual customer payments as the authoritative source of customer-derived income.

## In Scope
- Income visibility and summaries.
- Income derived from real customer payments.
- Payment-method and date/date-range filtering.
- Payment-type breakdown where useful.
- Dashboard integration using the same aggregation logic.
- OWNER read-only access.
- STAFF read access.
- Backend-authoritative financial aggregation.
- Automated tests and regression coverage.

## Out of Scope
- Double-entry accounting.
- GST automation.
- Payment gateways.
- Bank reconciliation/integration.
- Cloud accounting.
- Automatic income records unrelated to real customer payments.
- Payroll/settlement changes.
- WhatsApp/SMS.
- Duplicate payment or invoice systems.

## Core Guardrail
A customer payment contributes to income exactly once. Refunds reduce net income.
