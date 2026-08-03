# Phase 9 — Customer Billing & Invoice Foundation

## Status
PLANNING

## Goal
Implement customer-facing billing and invoice management for Saamu Tailors without changing finalized payroll, tailor settlement, income/expense history, or existing order workflows.

## In Scope
- Invoice generation from an existing order.
- Unique server-generated invoice numbers.
- Invoice line-item snapshots from order items.
- Customer and order linkage.
- Subtotal, total, amount paid and balance due.
- Customer payment records.
- Partial and full customer payments.
- Payment history and audit trail.
- Derived invoice status: UNPAID / PARTIALLY_PAID / PAID.
- OWNER read-only access.
- STAFF invoice/payment mutations.
- Frontend invoice list, invoice detail and payment recording.
- Backend tests, frontend static checks and manual verification.

## Explicitly Out of Scope
- Payment gateways.
- Bank API integrations.
- GST/tax accounting.
- Double-entry accounting.
- WhatsApp/SMS delivery.
- Automated email delivery.
- Refunds/credit notes.
- Bulk invoicing.
- Changes to finalized payroll or salary settlement.

## Guardrails
1. Existing Phase 1–8 functionality must continue working.
2. Existing order totals must not be silently rewritten.
3. Customer billing is separate from salary payroll.
4. Customer payment history is append-only.
5. Money calculations use Decimal.
6. Backend validation is authoritative.
7. OWNER can read but cannot mutate.
8. STAFF performs allowed mutations.
9. Anonymous users receive 401.
10. Financial history is never physically deleted.
