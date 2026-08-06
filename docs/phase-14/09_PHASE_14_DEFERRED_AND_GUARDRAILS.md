# Phase 14 — Deferred Items and Guardrails

## Deferred
Do not implement unless explicitly added to scope:
- Double-entry accounting.
- GST automation.
- Bank reconciliation.
- Bank/cloud accounting integrations.
- Payment gateways.
- Payroll redesign.
- Settlement redesign.
- WhatsApp/SMS.
- New invoice/payment systems.
- Manual financial history editing.
- Large-scale analytics infrastructure.
- Unrequested export/report formats.

## Guardrails
1. Reports are read-only.
2. Existing models remain authoritative.
3. Do not create duplicate financial records.
4. Income remains customer-payment-derived.
5. Refunds reduce net income.
6. Expenses remain separate from income.
7. Payroll and settlement remain authoritative in existing modules.
8. Backend calculations are authoritative.
9. Frontend does not calculate authoritative totals.
10. Do not perform unrelated refactoring.
