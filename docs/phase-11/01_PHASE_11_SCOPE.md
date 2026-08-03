# Phase 11 — Payments & Billing Scope

## Status
Planned — Version 1

## Objective
Implement the operational payment and billing layer for Saamu Tailors.

## In Scope
- Customer payments.
- Payment types:
  - ADVANCE
  - PARTIAL
  - FINAL
  - REFUND
- Track order total.
- Track amount paid.
- Track outstanding balance.
- Derive payment status from authoritative payment/order data.
- Digital bill generation containing:
  - Shop details
  - Customer details
  - Order details
  - Garment details
  - Payment details
  - Date/details required by the existing order workflow
- Integrate with the existing order/customer foundations.
- Preserve existing Phase 7 settlement/payroll behavior.

## Out of Scope
- PDF salary slips.
- WhatsApp/SMS delivery.
- Payment gateways.
- GST/accounting automation.
- Double-entry accounting.
- Automatic income-record creation unless already explicitly implemented by an earlier phase.
- Any changes to finalized payroll.

## Completion
Phase 11 is complete only when the scoped payment and billing workflows are implemented, tested, documented, and their manual-verification status is explicitly recorded.
