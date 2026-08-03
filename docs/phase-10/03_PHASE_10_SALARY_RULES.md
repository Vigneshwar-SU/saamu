# Phase 10 — Salary & Payroll Rules

## PER_GARMENT
`piece_rate_earnings = completed_quantity × applicable_rate_snapshot`

`gross_salary = piece_rate_earnings`

## FIXED_SALARY
`gross_salary = fixed_salary_amount_for_period`

## MIXED
`gross_salary = fixed_salary_amount_for_period + piece_rate_earnings`

## Advances and payments
Existing Phase 7 settlement remains authoritative.

`pending = gross_salary - advance_deductions - payments_recorded`

Pending must never become negative.

## Attendance
Attendance remains visible and aggregated as in Phase 6. Do not invent an attendance monetary deduction or bonus rule in Phase 10.

## Effective configuration
Salary configurations apply according to their effective dates. Finalized payroll retains the values used at calculation time.

## Validation
- Salary amounts cannot be negative.
- Payroll periods must have valid inclusive dates.
- Finalized periods cannot be recalculated.
- Existing overpayment and concurrency protections remain unchanged.
