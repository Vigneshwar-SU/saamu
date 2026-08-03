# Phase 11 — Frontend Specification

## Objective
Add the payment and digital-billing workflow to the existing React ERP UI.

## Requirements
- Reuse existing order/customer UI patterns.
- Display order total, paid amount, outstanding balance, and payment status.
- Provide STAFF controls for recording supported payment types.
- Provide appropriate validation and feedback.
- OWNER must see payment/billing information without mutation controls.
- Handle loading, empty, success, and error states.
- Use the existing API/service layer rather than duplicating HTTP configuration.
- Keep the established Saamu Tailors ERP design system.

## Digital Bill
Provide a bill view/component using real order data with:
- shop details
- customer details
- order details
- garment details
- payment details
- date

## Explicit Boundary
Do not add PDF generation or WhatsApp/SMS sending in Phase 11 unless those capabilities are already part of an existing completed implementation. They are later/deferred capabilities.
