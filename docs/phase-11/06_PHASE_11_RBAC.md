# Phase 11 — RBAC & Security

## Owner
OWNER is read-only for Phase 11 payment and billing information.

Allowed:
- View order payment totals.
- View payment history.
- View bill information.

Not allowed:
- Record payments.
- Modify payment records.
- Perform payment mutations.

## Staff
STAFF can:
- View payment/billing information.
- Record supported payments.
- Perform the permitted payment/billing mutations.

## Anonymous
Protected endpoints must reject anonymous requests.

## Enforcement
RBAC must be enforced by the backend. Frontend visibility is not a security boundary.

## Auditability
Payment actions should preserve the authenticated user where the existing project architecture supports audit fields.
