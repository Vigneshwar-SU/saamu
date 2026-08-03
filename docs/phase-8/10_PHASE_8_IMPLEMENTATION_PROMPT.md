# Phase 8 Implementation Prompt

You are implementing **Phase 8 of the Saamu Tailors Tailoring Management System**.

Read every file under `docs/phase-8/` first. Those files are the authoritative Phase 8 specification.

## Current Baseline
Phase 7 is PASS:
- 328 backend tests passing
- Django checks clean
- migrations clean
- Black/isort clean
- frontend lint/TypeScript/build clean
- Phase 7 pushed to `origin/master`

Do not redesign or restart previous phases.

## Goal
Implement:
1. Income records
2. Expense records
3. Dashboard financial summaries
4. Dashboard operational summaries
5. Date-range filtering
6. Backend RBAC
7. Frontend Dashboard, Income and Expenses
8. Tests and regression verification

## Backend
Create an appropriate isolated app following the existing project architecture.

Implement:
- models
- serializers
- views
- URLs
- migrations
- tests
- admin where consistent

Endpoints:
- `GET/POST /api/v1/income/`
- `GET /api/v1/income/{id}/`
- `GET/POST /api/v1/expenses/`
- `GET /api/v1/expenses/{id}/`
- `GET /api/v1/dashboard/summary/`

Use the existing error contract and pagination.

## RBAC
OWNER:
- read-only

STAFF:
- create income
- create expense
- read everything

Anonymous:
- 401

Backend enforcement is mandatory.

## Financial Integrity
- Decimal money arithmetic
- amount > 0
- inclusive date ranges
- no physical deletion of historical records
- `recorded_by` set from authenticated user
- finalized payroll/payment/advance history remains immutable
- dashboard is read-only

Dashboard must clearly distinguish:
- recorded income
- recorded expenses
- net recorded balance
- order revenue
- payroll paid
- salary advances
- workload

Do not invent tax or accounting rules.

## Frontend
Implement:
- Dashboard page
- Income page
- Expenses page
- Add Income dialog
- Add Expense dialog
- filters
- pagination
- OWNER read-only UI
- STAFF mutation controls
- navigation entries

Follow the established vertical-slice architecture and Saamu Tailors ERP styling.

## Testing
Run:
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

Add integration tests for authentication, RBAC, validation, filters, pagination, date boundaries, dashboard arithmetic, empty datasets and regression.

## Completion
Do not declare PASS until:
1. implementation is inspected
2. full backend suite passes
3. frontend lint passes
4. TypeScript passes
5. build passes
6. manual verification is completed
7. RBAC is verified
8. dashboard arithmetic is checked against source records
9. Git diff/status are clean
10. README and Phase 8 docs are updated
11. a Phase 8 completion report is written with summary, features, data model, APIs, RBAC, frontend, tests, manual verification, known issues, deferred items, changed files, Git verification and Phase 9 readiness

## Git
After verification:
- inspect `git diff`
- inspect `git status`
- create a meaningful Phase 8 commit
- push to `origin master`
- verify `HEAD == origin/master`
- verify clean working tree

## Do Not Implement
- tax/PF/ESI
- leave
- notifications
- customer billing/invoices
- payment gateways
- bank integrations
- Phase 9 features
- changes to finalized payroll

Keep Phase 8 additive, maintainable, tested and consistent with Phases 1–7.
