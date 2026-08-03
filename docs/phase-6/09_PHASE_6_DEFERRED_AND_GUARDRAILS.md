# Phase 6 — Deferred Items & Guardrails

## Deferred
- Leave management.
- Overtime.
- Shift/holiday scheduling.
- Biometric/GPS attendance.
- Fixed salary.
- Salary advances/deductions.
- Bonuses/incentives.
- Tax/PF/ESI.
- Salary transfer/bank/UPI.
- Payslip PDFs.
- Income/expense.
- Payments/billing/invoices.
- WhatsApp/SMS.
- Accounting integration.
- Dashboard analytics beyond Phase 6 needs.

## Guardrails
1. Preserve Phase 5 assignment lifecycle.
2. Preserve immutable rate snapshots.
3. Never calculate payroll from the current PieceRate.
4. Never count outstanding work as earned.
5. Never infer missing attendance as PRESENT.
6. Never invent salary rules.
7. OWNER remains read-only.
8. Anonymous remains denied.
9. Do not physically delete historical attendance/payroll records.
10. FINALIZED payroll must not be silently changed.
11. Keep local Windows/PostgreSQL compatibility.
12. Do not start Phase 7.
