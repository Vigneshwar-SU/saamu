# Phase 10 — Implementation Checklist

## Documentation
- [ ] Review every Phase 10 MD file.
- [ ] Review existing Phase 6 payroll implementation.
- [ ] Review existing Phase 7 settlement implementation.
- [ ] Confirm no duplicate payroll/payment functionality is introduced.

## Backend
- [ ] Implement salary configuration model/app as appropriate.
- [ ] Add migration.
- [ ] Add serializers/services/views/routes.
- [ ] Integrate salary models into payroll calculation.
- [ ] Preserve finalized-period immutability.
- [ ] Preserve existing advance/payment settlement logic.
- [ ] Add RBAC and audit handling.
- [ ] Add comprehensive tests.

## Frontend
- [ ] Add/update types.
- [ ] Add services/hooks.
- [ ] Add salary configuration UI.
- [ ] Enhance payroll detail.
- [ ] Preserve OWNER/STAFF behavior.
- [ ] Reuse existing settlement components.

## Verification
- [ ] Backend check.
- [ ] Migration check.
- [ ] Full pytest suite.
- [ ] Black.
- [ ] Isort.
- [ ] Frontend lint.
- [ ] TypeScript check.
- [ ] Production build.

## Phase closure
- [ ] Review implementation against every Phase 10 MD file.
- [ ] Review completion report.
- [ ] Resolve missing scope items.
- [ ] Git status clean.
- [ ] Commit Phase 10.
- [ ] Push to `origin/master`.
- [ ] Verify local HEAD equals `origin/master`.
- [ ] Close Phase 10 only after all required checks pass.
