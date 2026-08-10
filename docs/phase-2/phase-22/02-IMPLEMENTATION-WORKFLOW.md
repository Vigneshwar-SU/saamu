# Payments Completion — Implementation Workflow

1. Inspect the existing implementation before changing anything.
2. Identify what already works, what is incomplete, and what is broken.
3. Complete backend payment behavior and validation.
4. Run backend automated checks and tests.
5. Complete the frontend Payments workflow using existing project patterns.
6. Run TypeScript, lint, and production build checks.
7. Verify integration with Orders, Customers, Billing/Invoices, Income, and Dashboard.
8. Update completion documentation with changes and automated results.
9. Stop after Payments is implementation-complete.

Do not begin Settings in this task.

### Backend checklist
- ADVANCE / PARTIAL / FINAL / REFUND behavior
- Server-side amount validation
- Server-side order total, net paid, and outstanding calculations
- Safe refund handling
- Correct payment status
- OWNER read-only / STAFF management
- Meaningful API errors
- No unnecessary data reset

### Frontend checklist
- Payment list
- Recording form/modal/page
- Required fields and validation
- Payment history/details where applicable
- Correct status and balances
- Loading/empty/error/success states
- OWNER read-only UI

### Automated checks
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py migrate --plan`
- relevant/full backend tests
- frontend TypeScript check
- frontend lint
- frontend production build

Manual verification remains PENDING.
