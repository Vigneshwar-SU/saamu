# Phase 6 — Data Model

## Attendance
Suggested `apps/attendance/models.py` model:
- tailor → Tailor FK
- attendance_date → DateField
- status → PRESENT / ABSENT / HALF_DAY
- notes → optional
- marked_by → User FK
- timestamps

Constraint: unique `(tailor, attendance_date)`.

Historical attendance remains readable after a tailor is archived.

## PayrollPeriod
Suggested `apps/payroll/models.py` model:
- period_start
- period_end
- status: DRAFT / CALCULATED / FINALIZED
- notes
- created_by
- timestamps

Require `period_start <= period_end`.

## PayrollEntry
One entry per tailor/period:
- payroll_period
- tailor
- present_days
- half_days
- absent_days
- completed_pieces
- piece_rate_earnings
- attendance_amount
- total_payable
- timestamps

Do not create a monetary attendance rule unless explicitly configured. Default attendance amount may remain zero.

## Historical Integrity
Payroll uses:
`completed_quantity × rate_per_piece_snapshot`

It must not use the current PieceRate value, current order price, or measurement data.
