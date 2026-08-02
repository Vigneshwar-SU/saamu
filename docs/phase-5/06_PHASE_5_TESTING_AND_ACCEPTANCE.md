# Saamu Tailors — Phase 5 Testing & Acceptance

## Backend Commands
```text
python manage.py check
python manage.py migrate --check
python -m pytest
python -m black --check .
python -m isort --check-only .
```
All must pass.

## Tailor Tests
- Anonymous denied.
- OWNER read allowed; mutations denied.
- STAFF create/edit/archive/restore works.
- Archived tailor cannot receive new assignment.
- Historical assignments remain visible.

## Assignment Tests
- Valid assignment succeeds.
- Invalid tailor/order item rejected.
- Archived tailor rejected for new work.
- Customer/order-item mismatch rejected.
- Quantity <= 0 rejected.
- Quantity above remaining quantity rejected.
- Multiple assignments consume remaining quantity correctly.
- Remaining quantity is accurate.
- Completed quantity cannot exceed assigned quantity.

## Status Tests
- ASSIGNED → IN_PROGRESS succeeds.
- IN_PROGRESS → COMPLETED succeeds.
- Invalid/backward transitions rejected.
- Completed work cannot be incorrectly reopened unless explicitly supported.

## Piece Rate Tests
- Configurable rate works.
- Negative rate rejected.
- Assignment stores applicable rate snapshot.
- Later rate changes do not alter historical earnings.
- Earnings = completed quantity × snapshot rate.

## Earnings Tests
- Date, tailor and garment filters work.
- Completed quantity and earnings are correct.
- OWNER can read.
- STAFF can read.

## Frontend
```text
npm run lint
npx tsc --noEmit
npm run build
```

## Manual STAFF Walkthrough
1. Login STAFF.
2. Open Tailors.
3. Create/edit tailor.
4. Configure piece rate.
5. Select an existing order item.
6. Assign part/all of its remaining quantity.
7. Verify remaining quantity.
8. Move work to IN_PROGRESS.
9. Complete it.
10. Verify quantity and earnings.
11. Verify tailor detail.
12. Archive tailor and confirm new assignment is blocked.
13. Restore tailor.

## Manual OWNER Walkthrough
1. Login OWNER.
2. Open Tailors.
3. Verify tailors/workload/earnings are visible.
4. Verify mutation controls are absent.
5. Verify direct mutation APIs return 403.

## Regression
Verify customers, measurements, orders, and existing RBAC still work.
