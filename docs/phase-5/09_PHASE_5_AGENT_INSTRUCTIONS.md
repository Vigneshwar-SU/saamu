# Saamu Tailors — Phase 5 Agent Instructions

1. Read ALL Phase 5 markdown files before changing code.
2. Read relevant Phase 2, 3 and 4 implementation/docs.
3. Reuse existing architecture and conventions.
4. Do not rewrite working modules unnecessarily.
5. OWNER is view-only for business operations.
6. STAFF is the operational mutation role.
7. Backend permissions are authoritative.
8. Preserve historical order and measurement data.
9. Use Decimal for monetary values.
10. Preserve historical piece-rate snapshots.
11. Do not implement Phase 6+ features.
12. Do not silently expand scope.
13. Add backend tests for important business rules.
14. Run complete regression tests.
15. Run frontend lint/TypeScript/build.
16. Produce the Phase 5 completion report.
17. Do not commit/push until implementation and verification are reviewed by the project owner.

## Business Context
Customers bring cloth material, measurements are recorded, orders are created, and tailors perform stitching work. Phase 5 manages tailors and their workload/earnings around existing order items.

The system is currently for local shop deployment. Do not introduce cloud infrastructure.

## Stop Condition
After Phase 5 implementation and automated verification:
- write the completion report,
- report blockers honestly,
- STOP.

Do not start Phase 6 automatically.
