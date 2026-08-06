# Phase 13 — Manual Verification Checklist

Status: **NOT STARTED**

Automated tests do not count as manual verification.

## Checkpoint 1 — Income View
- [ ] Page loads.
- [ ] Summary values appear.
- [ ] Income/payment data is correct.
- [ ] No broken UI.

## Checkpoint 2 — Customer Payment
- [ ] Record a real customer payment through existing billing.
- [ ] Open Income.
- [ ] Confirm income increases by the correct amount.

## Checkpoint 3 — Payment Method
- [ ] Verify the income appears under the correct payment method.

## Checkpoint 4 — Refund
- [ ] Record a refund through existing billing.
- [ ] Confirm net income decreases correctly.

## Checkpoint 5 — Filters
- [ ] Date.
- [ ] Date range.
- [ ] Payment method.
- [ ] Other specified filters.

## Checkpoint 6 — Dashboard
- [ ] Dashboard income matches Income summary.
- [ ] Filtered income remains consistent.

## Checkpoint 7 — OWNER
- [ ] OWNER can view income.
- [ ] OWNER cannot mutate payments from Income.

## Checkpoint 8 — STAFF
- [ ] STAFF can view income.
- [ ] Existing billing permissions still work.

## Checkpoint 9 — Persistence
- [ ] Refresh.
- [ ] Navigate away/back.
- [ ] Values remain correct.

## Checkpoint 10 — Regression
- [ ] Expenses.
- [ ] Orders.
- [ ] Tailor assignment.
- [ ] Payroll.
- [ ] Invoices.
- [ ] Payments/refunds.
- [ ] Printable bill.

Do not mark this complete until a human performs the checks.
