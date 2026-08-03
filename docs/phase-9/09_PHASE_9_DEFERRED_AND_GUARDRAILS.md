# Phase 9 — Deferred Items & Guardrails

## Deferred
- GST/tax calculation.
- Tax invoices.
- Invoice PDF generation.
- WhatsApp/SMS delivery.
- Email delivery.
- Online payment gateways.
- Bank integrations.
- Refunds and credit notes.
- Double-entry bookkeeping.
- Customer credit limits.
- Bulk invoicing.
- Recurring billing.
- Advanced reports/exports.
- External payment reconciliation.

## Guardrails
1. Do not modify finalized payroll calculations.
2. Do not modify salary payment history.
3. Do not classify customer payments as salary payments.
4. Do not automatically insert income records unless explicitly defined by a later accounting rule.
5. Do not silently alter order totals.
6. Do not introduce tax logic without approved rules.
7. Do not physically delete invoices or customer payments.
8. Do not permit overpayment.
9. Do not trust frontend RBAC.
10. Do not weaken existing tests.

## Financial Separation
Customer billing is an operational billing layer. Phase 8 income/expense records remain separate unless a later phase explicitly defines reconciliation/accounting rules.
