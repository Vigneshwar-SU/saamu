# Phase 7 — Data Model

## Domain
Use a dedicated `apps/payments` app unless the existing architecture clearly dictates another domain name.

## SalaryAdvance
Fields:
- id
- tailor → Tailor (PROTECT)
- amount
- advance_date
- status: OUTSTANDING / DEDUCTED
- notes
- recorded_by → User (SET_NULL)
- created_at / updated_at

Amount must be positive. No delete endpoint. Historical records remain visible for archived tailors.

## PayrollPayment
Fields:
- id
- payroll_entry → PayrollEntry (PROTECT)
- tailor → Tailor (PROTECT)
- amount
- payment_date
- payment_method
- reference
- notes
- recorded_by → User (SET_NULL)
- created_at / updated_at

The payment tailor must match the payroll entry tailor.

## Settlement
Prefer derived values rather than mutable duplicated totals:
- gross_payable
- advance_deductions
- payments_recorded
- outstanding_payable
- settlement_status

Use transaction.atomic/select_for_update for settlement mutations so concurrent operations cannot overpay an entry.

## Integrity
Never change finalized payroll earnings. Never allow negative or overpaid settlement balances.
