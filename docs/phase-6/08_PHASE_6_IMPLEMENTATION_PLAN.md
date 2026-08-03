# Phase 6 — Implementation Plan

1. Inspect existing common, tailors, orders, permissions, exceptions, frontend services/hooks/routes.
2. Implement Attendance backend: model → migration → serializer → views → URLs → admin → tests.
3. Implement Payroll backend: period/entries → calculation → lifecycle → serializers/views/URLs → tests.
4. Run full backend regression.
5. Implement Attendance frontend using the existing vertical-slice pattern.
6. Implement Payroll frontend and detail views.
7. Run backend + frontend verification.
8. Perform browser manual verification.
9. Create `docs/phase-6/PHASE_6_COMPLETION_REPORT.md` with actual results.
10. Commit and push only after documentation is verified.

Suggested commit:
`feat(payroll): implement phase 6 attendance and payroll`

Verify:
```text
git rev-parse HEAD
git rev-parse origin/master
git status
```

Required final state:
- HEAD == origin/master
- working tree clean

Do not start Phase 7 in the same task.
