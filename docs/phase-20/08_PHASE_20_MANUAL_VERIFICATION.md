# Phase 20 — Manual Verification

**Status: NOT STARTED**

Automated tests do not count as manual verification.

## A. Local Regression
- [ ] Start backend using normal local PostgreSQL configuration.
- [ ] Confirm application starts normally.
- [ ] Log in as OWNER.
- [ ] Log in as STAFF.
- [ ] Confirm core existing pages work.

## B. Configuration
- [ ] Confirm .env is not committed.
- [ ] Confirm credentials are not displayed in startup/error output.
- [ ] Confirm environment-based database configuration can point at the expected PostgreSQL target.

## C. Migration Preparation
- [ ] Create a verified Phase 16 PostgreSQL backup.
- [ ] Confirm backup is outside the source tree.
- [ ] Confirm backup passes pg_restore --list.
- [ ] Confirm migration runbook is complete for the intended target.

## D. Cloud Target
Do NOT perform a live migration unless the operator intentionally chooses to do so.
- [ ] Provision a compatible PostgreSQL target.
- [ ] Transfer verified backup securely.
- [ ] Restore into target.
- [ ] Verify Django migrations.
- [ ] Verify representative customer/order/payment/finance/payroll records.
- [ ] Start Django against target.
- [ ] Perform smoke tests.

## E. Rollback
- [ ] Confirm original local environment remains intact.
- [ ] Confirm original local backup remains available.
- [ ] Confirm switching back to local configuration is possible.

## F. Security
- [ ] No credentials appear in UI/logs/errors.
- [ ] No destructive database controls are exposed through browser.
- [ ] No backup is served publicly by Django.
