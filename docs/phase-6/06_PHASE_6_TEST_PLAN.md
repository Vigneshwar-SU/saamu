# Phase 6 — Test & Acceptance Plan

## Backend
Run:
```text
python manage.py check
python manage.py migrate --check
python -m pytest
python -m black --check apps/ config/
python -m isort --check-only apps/ config/
```

## Attendance Tests
Cover:
- STAFF create/update.
- OWNER mutation 403.
- anonymous 401.
- duplicate tailor/date rejection.
- all three statuses.
- tailor/date/status filtering.
- archived tailor historical visibility.

## Payroll Tests
Cover:
- period creation and invalid date ranges.
- calculation.
- completed assignments included.
- IN_PROGRESS/outstanding excluded.
- inclusive date boundaries.
- historical rate snapshot invariance.
- multiple assignments/tailors aggregation.
- attendance aggregation.
- editable recalculation.
- FINALIZED recalculation blocked.
- OWNER reads / mutation 403 / anonymous 401.

## Frontend
Run:
```text
npm run lint
npx tsc --noEmit
npm run build
```

All Phase 1–5 regression tests must remain green.
