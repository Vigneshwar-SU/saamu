# Phase 6 — Frontend Specification

## Attendance
Route: `/attendance`

Provide:
- date, tailor and status filters
- pagination
- add/edit attendance dialogs
- loading/empty/error states
- OWNER read-only UI
- STAFF mutation controls

Table:
`Date | Tailor | Status | Notes | Marked By | Actions`

## Payroll
Route: `/payroll`

Show:
- period
- status
- completed pieces
- piece-rate earnings
- total payable
- actions

STAFF can create/calculate/finalize. OWNER can view.

## Payroll Detail
Route: `/payroll/:id`

Summary:
- period
- status
- completed pieces
- total earnings
- total payable

Tailor table:
`Tailor | Present | Half Day | Absent | Completed | Earnings | Payable`

Provide tailor-level detail with assignment earning breakdowns.

## UI
Use existing MUI/theme/layout patterns. Do not redesign the ERP shell.

Suggested structure:
`types/attendance.ts`, `types/payroll.ts`, services, hooks, dialogs, `Attendance.tsx`, `Payroll.tsx`, `PayrollDetail.tsx`.

Adapt to existing project conventions rather than duplicating infrastructure.
