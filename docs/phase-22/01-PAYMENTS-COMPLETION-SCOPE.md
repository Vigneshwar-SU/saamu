# Saamu Tailors — Payments Module Completion

## Objective
Complete and harden the Payments module without rebuilding functionality that already exists. Comprehensive manual verification will be performed later by the project owner.

## Business Rules
- Payment types: ADVANCE, PARTIAL, FINAL, REFUND.
- Order total is authoritative from order line items.
- Net paid is calculated server-side; refunds reduce net paid.
- Outstanding balance is calculated server-side.
- OWNER is view-only.
- STAFF can manage payments.
- Payment gateways, GST, and double-entry accounting are out of scope.

## Completion Requirements
### Backend
- Inspect existing payment models, migrations, serializers, views, services, URLs, and tests first.
- Reuse correct existing implementation.
- Complete missing CRUD/API behavior and server-side validation.
- Ensure refund, net-paid, outstanding, and status logic is authoritative.
- Enforce RBAC on mutating endpoints.
- Add/update automated tests.

### Frontend
- Complete the Payments UI and real API integration.
- Support required payment types and payment details.
- Show correct paid/refunded/outstanding information.
- Handle loading, empty, validation, API error, and success states.
- Keep OWNER read-only and STAFF management behavior consistent.

### Integration
Ensure Payments works correctly with Orders, Customers, Invoices/Billing, Income, and Dashboard financial summaries.

## Non-Goals
Do not add online payment gateways, GST/tax engine, double-entry accounting, unrelated redesigns, or unrelated refactors.
