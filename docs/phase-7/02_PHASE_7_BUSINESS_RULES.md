# Phase 7 — Business Rules

## Payroll Settlement
- Only FINALIZED payroll periods can be settled.
- Gross payable comes from the Phase 6 payroll entry.
- Payments reduce outstanding payable without changing payroll earnings.
- Payments plus applicable advance deductions must never exceed payable.
- Partial settlement remains payable.
- Fully settled entry has outstanding amount 0.

## Advances
- Every advance belongs to a tailor.
- Amount must be greater than zero.
- No physical deletion.
- An advance may be deducted against payroll only through an explicit operation.
- An advance cannot be deducted twice.
- A deduction cannot make payable negative.

## Payment Methods
Initial values:
- CASH
- BANK_TRANSFER
- UPI
- OTHER

A payment reference may be recorded where applicable.

## Audit
Record amount, date/time, tailor, payroll relation, method, reference, notes, recording user, and timestamps.

## Roles
OWNER: read-only.
STAFF: create advances, record payments, apply eligible advances.
Anonymous: 401.

## Money
Use Decimal/DecimalField only. Currency is INR.
