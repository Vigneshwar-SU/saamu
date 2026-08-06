# Phase 18 — Message Template Specification

## Purpose
Centralize customer-facing WhatsApp-ready templates.

## Rules
- Plain text and mobile-readable.
- No internal notes.
- No sensitive implementation details.
- No unsupported claims such as “sent”, “delivered”, or “paid”.
- Use exact backend-authoritative order/payment values.
- Never emit `undefined`, `null`, or malformed placeholders.

## Required Families

### Order Acknowledgement
Include when available:
- customer name;
- order/reference number;
- order date;
- concise order summary;
- total;
- advance/paid;
- balance;
- collection/delivery information when authoritative.

### Order Status Update
Include:
- customer name;
- order/reference number;
- current status;
- authoritative next-step information when available.

### Ready for Collection
Include:
- customer name;
- order/reference number;
- ready status;
- established collection instruction/location wording when available.

### Payment / Balance Summary
Include:
- customer name;
- order/reference when relevant;
- total;
- paid;
- balance;
- payment state.

## Implementation Rule
Template wording is centralized in the backend service and covered by tests. The frontend must not reconstruct financial/business calculations.
