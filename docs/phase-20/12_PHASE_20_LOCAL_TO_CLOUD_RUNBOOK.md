# Phase 20 — Local → Cloud Migration Runbook

This is an operator procedure, not an automated application feature.

## Before Migration
1. Stop active shop operations at a controlled point.
2. Create a final PostgreSQL custom-format backup using Phase 16 tooling.
3. Verify the backup with db_verify / pg_restore --list.
4. Preserve the original local database and backup.
5. Record current application configuration without exposing secrets.

## Prepare Target
1. Provision a compatible PostgreSQL database.
2. Create a restricted application database user appropriate for the target.
3. Configure required connection values through environment variables.
4. Do not commit target credentials.

## Transfer
Securely transfer the verified backup to the migration environment. Do not upload backups into a public/static directory.

## Restore
Restore using PostgreSQL tooling according to the Phase 16 runbook. Do not expose restore through Django.

## Verify
Check PostgreSQL connectivity, Django migrations, representative customers, orders, measurements, work assignments, payments/invoices, income/expenses, payroll, reports/exports, reminders, and communication preparation.

## Point Application to Target
Update deployment environment database settings, restart Django, and perform smoke tests.

## Rollback
If verification fails:
1. Stop using the cloud target.
2. Return application configuration to the known-good local target.
3. Preserve the failed target for investigation if appropriate.
4. Never delete the local source database until the cloud deployment is proven stable.

## Important Data Boundary
PostgreSQL backup contains database data only. It does not automatically include media/uploads, static/build output, .env/secrets, logs, or source code. These must be handled separately in any future production deployment plan.
