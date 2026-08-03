# Phase 10 — Data Model

## Tailor Salary Configuration

Suggested fields:
- `tailor`
- `salary_model`: `PER_GARMENT`, `FIXED_SALARY`, `MIXED`
- `fixed_salary_amount`
- `effective_from`
- `effective_to` nullable
- `is_active`
- `notes`
- `created_by`
- timestamps

Rules:
- `fixed_salary_amount >= 0`.
- Fixed and mixed models require a valid fixed amount.
- Configuration changes must not rewrite finalized payroll.
- Historical configurations must remain reproducible.

## PayrollEntry extension

Expose/store explicit salary components as appropriate:
- `fixed_salary_amount`
- `piece_rate_earnings`
- `gross_salary`
- `advance_deductions`
- `total_payable`

Do not duplicate Phase 7 payment history or settlement state.

## Historical integrity

When a calculation depends on a salary configuration, snapshot the values used on the payroll entry so later configuration changes cannot alter finalized history.
