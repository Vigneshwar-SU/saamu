# Phase 6 — Business Rules

## Attendance
One record per tailor/date.
Statuses:
- PRESENT
- ABSENT
- HALF_DAY

Missing records are not assumed to be PRESENT.

## Earnings
For every completed assignment:
`earned = completed_quantity × rate_per_piece_snapshot`

For a tailor:
`piece_rate_earnings = SUM(earned)`

IN_PROGRESS/outstanding work earns zero until completed.

## Period Boundary
Payroll periods are inclusive:
`period_start <= earning_date <= period_end`

Use the assignment completion date/timestamp, not order creation date.

## Rate Snapshot
If an assignment was created at ₹125 and later the current piece rate becomes ₹150, completing 3 pieces still earns ₹375.

## Lifecycle
`DRAFT → CALCULATED → FINALIZED`

DRAFT can be calculated. CALCULATED can be recalculated while editable. FINALIZED is immutable through normal operations.

## Example
Assignment A: 5 assigned, 3 completed, snapshot ₹125.
Assignment B: 4 assigned, 4 completed, snapshot ₹150.

Completed = 7 pcs.
Outstanding = 2 pcs.
Earnings = `(3×125)+(4×150) = ₹975`.
