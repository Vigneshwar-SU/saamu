# Phase 9 — Billing Rules

## Invoice Creation
1. Invoice must reference an existing order.
2. Only one invoice may exist for an order unless an explicitly approved rule says otherwise.
3. Invoice number is generated server-side and unique.
4. Invoice item values are snapshots from the order.
5. Money calculations use Decimal.
6. Creation is atomic.

## Amount Rules
- Amounts cannot be negative.
- Customer payments must be > 0.
- A payment cannot exceed the current balance.
- Exact payment of the balance produces PAID.
- Multiple partial payments are allowed.

## Payment Rules
- Payments are append-only.
- No update/delete endpoint.
- `recorded_by` comes from the authenticated user.
- Payment method is controlled by backend choices.

## Status
Status is derived from payment totals and must not become stale.

## Historical Integrity
- Invoice snapshots do not change when the order changes later.
- Payment history is never physically deleted.
- Payroll and customer billing remain independent.

## Concurrency
Customer payment creation must use `transaction.atomic()` and `select_for_update()` on the invoice so concurrent requests cannot overpay it.

## RBAC
- Anonymous: 401.
- OWNER: read only.
- STAFF: invoice creation and payment recording.
