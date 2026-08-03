# Phase 6 — Manual Verification Checklist

## STAFF
- [ ] Login succeeds.
- [ ] Attendance page loads.
- [ ] Payroll page loads.
- [ ] No console errors.

## Attendance
- [ ] Create PRESENT.
- [ ] Create HALF_DAY.
- [ ] Create ABSENT.
- [ ] Edit attendance.
- [ ] Tailor/date/status filters work.
- [ ] Duplicate tailor/date is rejected.

## Payroll
- [ ] Create a period.
- [ ] Calculate it.
- [ ] Completed pieces and earnings are correct.
- [ ] Attendance summary is correct.
- [ ] Outstanding pieces are excluded from earnings.
- [ ] Historical rate snapshot remains unchanged after current PieceRate changes.
- [ ] Finalize works.
- [ ] Normal recalculation/mutation is blocked after FINALIZED.

## OWNER
- [ ] Attendance is readable.
- [ ] Payroll is readable.
- [ ] Attendance mutations are hidden/403.
- [ ] Payroll create/calculate/finalize controls are hidden/403.

## Anonymous
- [ ] Attendance API returns 401.
- [ ] Payroll API returns 401.

## UI
- [ ] Desktop layout.
- [ ] Short viewport scrolling.
- [ ] Sidebar open + page scrolling.
- [ ] Loading/empty/error states.
- [ ] No horizontal overflow.
