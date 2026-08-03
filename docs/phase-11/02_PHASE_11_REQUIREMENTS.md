# Phase 11 — Functional Requirements

## 1. Payment Recording
Staff must be able to record payments against an order.

Supported payment types:
- Advance
- Partial
- Final
- Refund

Each payment must retain the information necessary to audit the transaction.

## 2. Financial Totals
The system must expose:
- Order total
- Total paid
- Outstanding balance
- Payment status

These values must be derived consistently from authoritative backend data.

## 3. Payment Rules
- Payments must be validated server-side.
- Refunds must be represented explicitly as refunds rather than silently altering historical payment records.
- The backend must prevent invalid financial states.
- Existing settlement/payroll rules must not be duplicated or broken.

## 4. Digital Bill
A digital bill must provide the customer-facing order/payment summary, including:
- Shop information
- Customer information
- Order information
- Garments
- Payment information
- Date

The bill must use real database data.

## 5. Roles
- STAFF: manage payments and billing operations.
- OWNER: view payment/billing information according to the established read-only role.
- Anonymous users: no access to protected payment/billing operations.
