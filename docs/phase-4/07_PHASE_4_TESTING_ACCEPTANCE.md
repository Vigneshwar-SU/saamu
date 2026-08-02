# Saamu Tailors — Phase 4 Testing & Acceptance Criteria

## Backend
Run:
```text
python manage.py check
python manage.py migrate --check
python -m pytest
python -m black --check .
python -m isort --check-only .
```
All previous Phase 0–3 tests must remain green.

Test orders, garment items, measurement snapshot/history, lifecycle, status history, validation, OWNER 403 mutations, STAFF mutations and anonymous denial.

## Frontend
Run:
```text
npm run lint
npx tsc --noEmit
npm run build
```

## Manual STAFF flow
Login → Orders → find customer → create order → add SHIRT/PANT → select measurement → save → list → detail → valid status transitions → refresh → verify persistence.

Update customer measurements afterwards and verify the old order's measurement version/snapshot remains unchanged.

## Manual OWNER flow
Login as OWNER → Orders → list/detail visible → mutation controls absent → backend mutation attempt returns 403 → page scrolls normally.

## Acceptance
Complete only when implementation, tests, manual verification, completion report and Git push are done.
