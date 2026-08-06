# Phase 15 — Manual Verification Checklist

Status: NOT STARTED

## A. Authentication
- [ ] Login with valid STAFF credentials.
- [ ] Login with valid OWNER credentials.
- [ ] Invalid login is rejected.
- [ ] Logout works.
- [ ] Expired/invalid session is handled cleanly.

## B. Core Operations
- [ ] Dashboard loads.
- [ ] Orders list/detail works.
- [ ] Customer creation/detail/measurements work.
- [ ] Tailor/work assignment flows work.
- [ ] Payroll and salary flows work.
- [ ] Expense creation/filtering/summary works.
- [ ] Payment/invoice flows work.
- [ ] Income reflects customer payments and refunds.
- [ ] Reports match corresponding operational/financial pages.

## C. RBAC
- [ ] OWNER read-only behavior verified.
- [ ] STAFF mutation behavior verified.
- [ ] Direct API mutation attempts as OWNER are rejected.

## D. Reliability
- [ ] Network/API error displays useful feedback.
- [ ] Empty states display correctly.
- [ ] Loading states do not freeze the page.
- [ ] Retry works after a temporary failure.
- [ ] Refreshing after mutations preserves correct data.

## E. Backup
- [ ] Database backup created.
- [ ] Backup file exists at the documented location.
- [ ] Restore procedure tested safely.
- [ ] Restored data verified.

## F. Final
- [ ] No blocking console errors.
- [ ] Production build succeeds.
- [ ] Full regression tests pass.
