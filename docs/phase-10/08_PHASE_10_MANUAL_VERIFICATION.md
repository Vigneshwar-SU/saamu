# Phase 10 — Manual Verification Checklist

This checklist is retained for the designated manual-verification point.

## Salary configuration
- [ ] STAFF creates PER_GARMENT configuration.
- [ ] STAFF creates FIXED_SALARY configuration.
- [ ] STAFF creates MIXED configuration.
- [ ] Invalid salary values are rejected.
- [ ] OWNER can view but cannot mutate.

## Payroll
- [ ] Create a payroll period.
- [ ] Calculate PER_GARMENT salary and verify completed pieces × rate.
- [ ] Calculate FIXED_SALARY salary and verify fixed component.
- [ ] Calculate MIXED salary and verify both components.
- [ ] Verify gross salary.

## Settlement
- [ ] Apply an existing salary advance.
- [ ] Record a partial salary payment.
- [ ] Verify pending amount.
- [ ] Settle the remaining amount.
- [ ] Verify SETTLED status.
- [ ] Verify finalized payroll remains unchanged.

## RBAC
- [ ] OWNER sees salary/payroll information but no mutation controls.
- [ ] STAFF sees required mutation controls.
- [ ] Anonymous access is rejected.

## Regression
- [ ] Orders remain intact.
- [ ] Invoices remain intact.
- [ ] Customer payments remain intact.
- [ ] Income/expense data remains intact.
- [ ] Attendance/payroll/advance/payment data remains intact.
