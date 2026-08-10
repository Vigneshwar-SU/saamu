# Phase 22 — Automated Test Plan

## Backend
Run the complete backend suite.

Minimum coverage:
- Settings retrieval
- Valid update
- Invalid values
- Persistence
- Permission behavior
- Unauthenticated access
- Existing billing/shop-details regression

## Frontend
Run:
```text
npm run lint
npx tsc --noEmit
npm run build
```
Also run existing frontend tests if present.

## Django / Migration
Run:
```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

Do not weaken or delete tests to make the phase pass.
