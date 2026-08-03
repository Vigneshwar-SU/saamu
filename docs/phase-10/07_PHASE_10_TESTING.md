# Phase 10 — Testing Specification

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

## Required backend tests

### Salary configuration
- PER_GARMENT valid configuration.
- FIXED_SALARY valid configuration.
- MIXED valid configuration.
- Negative/invalid amounts rejected.
- Required fixed salary validation.
- Effective-date validation.
- OWNER mutation rejected.
- Anonymous 401.

### Payroll
- PER_GARMENT calculation.
- FIXED_SALARY calculation.
- MIXED calculation.
- Multiple tailors with different models.
- Historical rate/configuration snapshot.
- Configuration changes do not rewrite finalized payroll.
- Inclusive period boundaries.
- In-progress/outstanding pieces excluded from completed-piece earnings.

### Settlement regression
- Advance deduction reduces payable.
- Payments reduce pending amount.
- Exact final payment reaches SETTLED.
- Overpayment remains impossible.
- Existing concurrency test remains green.

All Phase 1–9 tests must continue passing.
