# Phase 19 — Testing Specification

Focused coverage must include:
1. Eligible and ineligible states.
2. Every implemented reminder type.
3. Agreement with authoritative order/payment services.
4. Agreement with Phase 18 message preparation.
5. Phone normalization and missing recipients.
6. RBAC and HTTP contracts.
7. Duplicate-prevention/idempotency.
8. No unintended business-data mutation.
9. Privacy/logging safeguards.
10. Frontend loading/error/retry/duplicate protection where applicable.

Regression gates:
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused tests
- full backend suite
- Black
- isort
- frontend lint
- TypeScript
- frontend build
