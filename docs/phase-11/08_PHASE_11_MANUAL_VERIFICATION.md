# Phase 11 — Manual Verification Checklist

## Important
Automated tests do not count as manual verification.

Do not mark this checklist complete unless the flows have actually been exercised manually.

## Payment Flow
- [ ] Open an existing order as STAFF.
- [ ] Confirm order total is displayed correctly.
- [ ] Record an ADVANCE payment.
- [ ] Confirm paid amount and balance update.
- [ ] Record a PARTIAL payment.
- [ ] Confirm totals/status update.
- [ ] Record a FINAL payment where valid.
- [ ] Confirm balance/status becomes correct.
- [ ] Verify REFUND handling.
- [ ] Confirm payment history remains visible/auditable.

## Bill Flow
- [ ] Open the digital bill.
- [ ] Verify shop details.
- [ ] Verify customer details.
- [ ] Verify order details.
- [ ] Verify garment details.
- [ ] Verify payment details.
- [ ] Verify date.
- [ ] Confirm totals match the order/payment records.

## RBAC
- [ ] STAFF can perform payment mutations.
- [ ] OWNER can view payment/bill information.
- [ ] OWNER cannot mutate payment information.
- [ ] Anonymous access is rejected.

## Regression
- [ ] Existing order workflow still works.
- [ ] Existing payroll/settlement workflow still works.

## Final Status
Record one:
- NOT STARTED
- IN PROGRESS
- PASS
- PASS WITH LIMITATIONS
- FAIL
