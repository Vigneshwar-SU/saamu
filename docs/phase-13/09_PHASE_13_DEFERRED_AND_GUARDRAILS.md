# Phase 13 — Deferred Items and Guardrails

## Deferred
Do not implement:
- Double-entry accounting.
- GST automation.
- Payment gateways.
- Bank reconciliation/APIs.
- Cloud accounting.
- Automatic accounting journals.
- WhatsApp/SMS.
- Payroll changes.
- Salary settlement changes.
- Duplicate invoice/payment systems.

## Guardrails
1. Do not create duplicate income records for customer payments.
2. Actual customer payments remain authoritative.
3. Refunds reduce net income.
4. Frontend calculations are presentation-only.
5. Income viewing must not bypass payment/refund permissions.
6. Do not perform unrelated refactoring.
7. Preserve Phase 12 Expense Management as a separate financial concept.
