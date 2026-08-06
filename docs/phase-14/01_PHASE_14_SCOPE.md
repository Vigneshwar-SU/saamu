# Phase 14 — Reports & Business Insights: Scope

## Objective
Build a read-only reporting and business-insights layer for Saamu Tailors using authoritative data from previous phases.

## In Scope
- Business overview/reporting page.
- Order performance insights.
- Customer insights.
- Tailor workload insights.
- Income and expense comparison.
- Payment/refund-aware financial reporting.
- Date/date-range filtering.
- Server-side aggregation.
- OWNER and STAFF read access.
- Reusable reporting services.
- Automated tests and regression coverage.
- Frontend reporting UI.

## Out of Scope
- Accounting automation.
- Double-entry accounting.
- GST automation.
- Payment gateways.
- Bank/cloud accounting integration.
- Payroll/settlement changes.
- New payment/invoice systems.
- WhatsApp/SMS.
- Export/PDF generation unless already required by existing architecture.
- Manual editing of financial history.

## Core Guardrail
Reports are derived from existing authoritative records. The reporting layer must never become a second source of truth.
