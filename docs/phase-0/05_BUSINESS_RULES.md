# Saamu Tailors — Business Rules

This document defines rules that should guide backend validation and business logic.

## Customer rules

1. A customer can have multiple orders.
2. Customer history must be preserved.
3. Phone number should be searchable.
4. Do not silently create duplicate customers when an existing customer can be identified.
5. Customer deletion should be treated carefully because historical orders/payments may depend on the customer.

## Order rules

1. An order belongs to a customer.
2. One order can contain multiple garment/order items.
3. Each order should have a unique human-readable order number.
4. An order item represents a garment type and quantity.
5. Measurements used for an order must be preserved historically.
6. Updating a customer's latest measurement must not alter historical measurements already used by completed/old orders.
7. Order totals must be calculated consistently.
8. Payment records must not allow invalid totals.
9. Balance should be derived from order/payment information.
10. Delivered orders should retain their historical information.
11. Cancellation must preserve audit/history where applicable.

## Measurement rules

1. Different garment types may require different measurements.
2. Measurements should be associated with the relevant order/item snapshot.
3. Previous measurements may be copied into a new order as a starting point.
4. Copying previous measurements must create a new snapshot rather than modifying the old one.

## Payment rules

1. Payments belong to a customer/order context.
2. Every payment must have an amount and date/time.
3. Payment amount must be positive unless a separate refund model/process is explicitly used.
4. The system must prevent payments from causing an invalid balance.
5. Customer payment records are the source for income calculations.
6. Do not ask staff to record the same payment separately as both "payment" and "income".

## Expense rules

1. Every expense has an amount and date.
2. Expense category should be recorded where applicable.
3. Expense records must identify who recorded them.
4. Financial records should not be physically deleted without a strong reason; prefer controlled reversal/void mechanisms for important financial data.

## Tailor rules

1. A tailor can have multiple assigned garments.
2. Workload should be calculated from active work.
3. Completed work should remain in history.
4. Tailor salary records must be traceable to a period/payment.

## Order status rules

The exact state machine will be finalized during implementation, but the process should represent the real workflow:

```text
New
  ↓
Cutting
  ↓
Tailor / Stitching
  ↓
Ironing
  ↓
Ready for Collection
  ↓
Collected / Delivered
```

Not every order necessarily requires every stage.

Cancelled orders must be distinguishable from completed orders.

## Locker rules

1. Only ready/appropriate garments should be assigned to collection storage.
2. Locker/location information should identify where the garment is stored.
3. Collection should release the locker/location assignment.
4. Historical storage information should remain available when useful.

## Dashboard rules

Dashboard numbers must be calculated from actual records.

Do not maintain duplicate manually entered dashboard totals.

## Financial reporting rules

At minimum:

```text
Customer payments → Income
Recorded expenses → Expenses
Income - Expenses → Net amount
```

The exact accounting interpretation of "income" and "net" should be documented before financial reporting is finalized.

## Audit rules

Important actions should record:

- User
- Action
- Entity/type
- Entity ID
- Timestamp
- Relevant context

## Data integrity rule

Financial and historical operational data should not be casually hard-deleted.

Prefer:

- status changes
- cancellation
- reversal
- archival
- audit records

where appropriate.
