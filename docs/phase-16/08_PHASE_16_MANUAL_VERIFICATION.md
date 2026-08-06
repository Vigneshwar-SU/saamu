# Phase 16 — Manual Verification

**Status: NOT STARTED**

## Backup
- [ ] Create a real backup using the production/local PostgreSQL installation.
- [ ] Confirm timestamped backup appears in the configured backup location.
- [ ] Confirm the backup file has a non-zero size and can be inspected by PostgreSQL tooling.
- [ ] Confirm no credentials/secrets are exposed.
- [ ] Confirm backup does not interrupt normal shop operation unexpectedly.

## Restore safety
- [ ] Confirm restore requires explicit confirmation.
- [ ] Confirm a pre-restore safety backup is created where applicable.
- [ ] Perform a restore ONLY against a throwaway/test database first.
- [ ] Verify expected customers/orders/payments/expenses/payroll data after test restore.
- [ ] Verify application can reconnect after restoration.
- [ ] Confirm a failed restore does not silently report success.

## Portability
- [ ] Restore a test backup into a separate PostgreSQL instance/database.
- [ ] Verify application compatibility with the restored database.
- [ ] Verify documented local → cloud migration steps are realistic.

## Regression
- [ ] Authentication
- [ ] OWNER/STAFF RBAC
- [ ] Orders
- [ ] Customers
- [ ] Tailors
- [ ] Billing/payments/refunds
- [ ] Income
- [ ] Expenses
- [ ] Payroll/advances
- [ ] Reports
- [ ] Dashboard

Do not change this status automatically after automated tests.
