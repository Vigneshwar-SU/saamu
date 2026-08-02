# Testing Strategy

## Objective
Establish reliable testing before business logic.

## Backend
Prefer:
```text
pytest
pytest-django
```
or the justified testing approach already established by Phase 0.

## Required Verification
Run:
```text
python manage.py check
pytest
```

Verify:
- Django starts
- PostgreSQL configuration works
- No silent SQLite fallback exists
- Health endpoint works
- Standard API error handling works where practical

Health endpoint:
```text
GET /api/v1/health/
```

## Frontend
Run:
```text
npm run build
npx tsc --noEmit
npm run lint
```

## Manual
Verify:
1. Backend starts.
2. Frontend starts.
3. Frontend can reach backend health endpoint.
4. Health endpoint returns expected JSON.
5. No business functionality was accidentally implemented.

## Quality
Do not create meaningless tests just for coverage.

## Failure Reporting
For every failed/unavailable command record command, reason, status, and remaining action.

Statuses:
```text
PASS
FAIL
BLOCKED
```
