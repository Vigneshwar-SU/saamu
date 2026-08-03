# Phase 8 — Testing & Acceptance

## Backend commands
```text
python manage.py check
python manage.py migrate --check
python -m pytest
python -m black --check .
python -m isort --check-only .
```

## Required coverage
- anonymous 401
- OWNER read 200 / mutation 403
- STAFF create success
- positive amount validation
- required category/date validation
- filters and pagination
- inclusive date boundaries
- income totals
- expense totals
- net balance
- payroll payment aggregation
- order status counts
- garment totals
- tailor workload
- empty datasets
- full Phase 1–7 regression

## Frontend
```text
npm run lint
npx tsc --noEmit
npm run build
```
