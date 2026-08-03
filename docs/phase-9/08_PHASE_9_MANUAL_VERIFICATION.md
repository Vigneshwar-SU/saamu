# Phase 9 — Manual Verification Checklist

## Preparation
- [ ] Start PostgreSQL.
- [ ] Start Django backend.
- [ ] Start Vite frontend.
- [ ] Login as STAFF.
- [ ] Ensure an existing customer and order exist.

## Invoice Flow
- [ ] Open Invoices.
- [ ] Create an invoice from an existing order.
- [ ] Verify customer/order details.
- [ ] Verify every invoice item.
- [ ] Verify subtotal and total.
- [ ] Verify unique invoice number.
- [ ] Refresh and confirm persistence.
- [ ] Attempt duplicate invoice and verify rejection.

## Payment Flow
- [ ] Open invoice detail.
- [ ] Record partial payment.
- [ ] Verify paid increases.
- [ ] Verify balance decreases.
- [ ] Verify PARTIALLY_PAID.
- [ ] Record another payment.
- [ ] Pay exact remaining balance.
- [ ] Verify PAID.
- [ ] Verify payment history.

## Validation
- [ ] Zero payment rejected.
- [ ] Negative payment rejected.
- [ ] Payment greater than balance rejected.

## OWNER
- [ ] Login OWNER.
- [ ] View invoice list.
- [ ] View invoice detail.
- [ ] View payment history.
- [ ] Create action hidden.
- [ ] Record Payment hidden.
- [ ] Direct mutation attempt returns 403.

## Regression
- [ ] Customers.
- [ ] Measurements.
- [ ] Orders.
- [ ] Tailors/workload.
- [ ] Attendance.
- [ ] Payroll.
- [ ] Salary settlement.
- [ ] Income/expenses.
- [ ] Dashboard.

## Final
- [ ] Backend tests pass.
- [ ] Frontend lint passes.
- [ ] TypeScript passes.
- [ ] Build passes.
- [ ] Git clean.
- [ ] Commit created.
- [ ] Push successful.
