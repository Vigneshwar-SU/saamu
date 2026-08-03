# Phase 7 Implementation Prompt

You are working on the existing **Saamu Tailors** repository.

Implement **Phase 7 — Salary Payments, Advances & Payroll Settlement** strictly according to the documents in `docs/phase-7/`.

## Existing Context
Phases 1–6 are implemented and verified:
- Customers + measurements
- Orders + immutable measurement snapshots
- Tailors + piece-rate assignments
- Attendance
- Payroll calculation/finalization

Do not rebuild or replace existing functionality.

## Goal
Extend finalized payroll into an auditable settlement workflow:
- tailor salary advances
- payroll payments
- partial/full settlement
- outstanding payable
- payment history
- OWNER read-only / STAFF mutation

## Rules
1. Read all Phase 7 docs before coding.
2. Inspect existing architecture and reuse established patterns.
3. Do not invent unrelated features.
4. Finalized payroll earnings must remain immutable.
5. Use Decimal for all money.
6. Use transaction.atomic/select_for_update where needed to prevent concurrent overpayment.
7. No physical deletion of financial history.
8. Backend RBAC is authoritative.
9. Frontend role checks are UX only.
10. Preserve all Phase 1–6 behavior.
11. Do not implement deferred features.
12. Follow the established vertical-slice frontend architecture.

## Backend
Implement the appropriate payments/advances domain app:
- models
- migrations
- serializers
- views/viewsets
- URLs
- admin
- permissions
- settlement calculations
- concurrency-safe payment recording
- complete tests

## Frontend
Implement:
- Advances page
- payroll settlement information
- payment history
- record-payment dialog
- advance application workflow
- gross/advance/paid/outstanding values
- OWNER view-only UI
- STAFF mutation UI
- routes/navigation
- loading/error/empty states

## Verification
Run all commands in `docs/phase-7/07_PHASE_7_TESTING_ACCEPTANCE.md`.

Then perform the complete manual browser walkthrough.

## Documentation
After implementation:
- update README if appropriate
- complete `docs/phase-7/09_PHASE_7_COMPLETION_REPORT_TEMPLATE.md`
- save final report as `docs/phase-7/PHASE_7_COMPLETION_REPORT.md`
- record actual test counts, commands, manual results, known issues, and deferred items honestly

## Git
Only after all verification passes:
```powershell
git status
git add .
git commit -m "feat(payments): implement phase 7 payroll settlement"
git push origin master
git fetch origin
git rev-parse HEAD
git rev-parse origin/master
git status
```

Do not claim completion until tests, manual verification, documentation, push, HEAD equality, and clean working tree are all confirmed.

Stop after Phase 7. Do not start Phase 8.
