# Phase 18 — Testing Specification

## Backend Gates
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused communication tests
- full pytest suite
- Black check
- isort check

## Required Tests
1. All message templates.
2. Deterministic output.
3. Authoritative order/customer/payment values.
4. Exact money formatting.
5. Missing optional fields.
6. Missing/invalid phones.
7. Phone normalization.
8. WhatsApp URL encoding.
9. Privacy exclusions.
10. Anonymous authorization.
11. OWNER/STAFF authorization.
12. Read-only behavior.
13. No business-record mutation.

## Frontend Gates
- `npm run lint`
- `npx tsc --noEmit`
- `npm run build`

Do not weaken existing tests.
