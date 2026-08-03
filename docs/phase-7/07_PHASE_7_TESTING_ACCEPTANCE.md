# Phase 7 — Testing & Acceptance

## Required Commands
```powershell
cd backend
python manage.py check
python manage.py migrate --check
python -m pytest
python -m black --check apps/ config/
python -m isort --check-only apps/ config/

cd ../frontend
npm run lint
npx tsc --noEmit
npm run build
```

## Backend Acceptance
### Advances
- STAFF create succeeds.
- OWNER create → 403.
- Anonymous → 401.
- Amount must be > 0.
- Archived-tailor history remains visible.
- No physical delete.

### Payments
- Only FINALIZED payroll can receive payments.
- Positive amount required.
- Overpayment rejected.
- Correct tailor relationship enforced.
- Multiple partial payments work.
- Exact final payment gives outstanding 0.
- Decimal arithmetic is exact.
- Payment history is preserved.

### Settlement
- Gross payable matches Phase 6.
- Advance is applied once.
- Payment reduces outstanding.
- Fully settled status is correct.
- Concurrent operations cannot overpay.

### RBAC
OWNER reads 200 / mutations 403.
STAFF mutations 200/201.
Anonymous 401.

## Frontend
- lint clean
- TypeScript clean
- build succeeds

## Manual Browser Walkthrough
1. STAFF login.
2. Open finalized payroll.
3. Verify gross payable.
4. Create tailor advance.
5. Apply eligible advance.
6. Verify outstanding decreases.
7. Record partial payment.
8. Verify paid/outstanding.
9. Record final payment.
10. Verify settled state.
11. Login OWNER.
12. Verify information is visible but mutation controls are absent.
13. Smoke-test Customers, Orders, Tailors, Measurements, Attendance, and Payroll.
