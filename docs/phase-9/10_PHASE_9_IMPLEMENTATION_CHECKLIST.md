# Phase 9 — Implementation Checklist

## Before Coding
- [ ] Read relevant Phase 1–8 docs.
- [ ] Inspect current repository architecture.
- [ ] Confirm API/error/pagination conventions.
- [ ] Confirm RBAC helpers.
- [ ] Confirm Order/OrderItem relationships.
- [ ] Confirm existing frontend vertical-slice patterns.

## Backend
- [ ] Create a clearly scoped billing/invoice app.
- [ ] Add models and migration.
- [ ] Add serializers.
- [ ] Add invoice creation/payment services.
- [ ] Add views/routes.
- [ ] Register app/settings/URLs.
- [ ] Implement transactional payment locking.
- [ ] Implement RBAC.
- [ ] Add tests.

## Frontend
- [ ] Add billing types.
- [ ] Add service layer.
- [ ] Add React Query hooks.
- [ ] Add invoice list.
- [ ] Add invoice detail.
- [ ] Add create invoice action/dialog.
- [ ] Add record payment dialog.
- [ ] Add order integration.
- [ ] Add navigation.
- [ ] Hide mutation controls for OWNER.

## Quality Gates
```text
python manage.py check
python manage.py migrate --check
python -m pytest
python -m black --check .
python -m isort --check-only .
npm run lint
npx tsc --noEmit
npm run build
```

## Completion Report
Create `PHASE_9_COMPLETION_REPORT.md` with:
- PASS/FAIL status.
- Features.
- Data model.
- API endpoints.
- Business rules.
- RBAC.
- Frontend.
- Tests.
- Manual verification.
- Known issues.
- Deferred items.
- Files changed.
- Git verification.
- Phase 10 readiness.

Do not mark PASS unless the required regression and quality gates pass.
