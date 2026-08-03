# Phase 9 — RBAC & Security

## OWNER
Allowed:
- Invoice list/detail.
- Payment history.
- Billing totals.

Denied:
- Create invoice.
- Record payment.
- Any invoice/payment mutation.

Expected response: 403.

## STAFF
Allowed:
- Create invoice.
- View invoices.
- Record customer payments.
- View payment history.

## Anonymous
All invoice/payment endpoints require authentication.

Expected response: 401.

## Backend Authority
Frontend controls are convenience only. Every mutation permission must be enforced server-side.

## Audit
- Invoice creator comes from the authenticated user.
- Payment recorder comes from the authenticated user.
- Client input cannot override audit identity.

## Financial Safety
- Prevent overpayment.
- Prevent duplicate invoice creation.
- Prevent negative balances.
- Use database constraints where practical.
- Use transactional locking for payment mutation.
