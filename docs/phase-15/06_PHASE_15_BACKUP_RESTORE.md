# Phase 15 — PostgreSQL Backup & Restore

## Objective
Make local-shop data recoverable before Version 1 is treated as operationally ready.

## Deliverables
- Documented PostgreSQL backup command/workflow.
- Documented restore workflow.
- Backup location recommendation outside the application source directory.
- Naming convention containing date/time.
- Restore verification using a non-production/test database where practical.
- Documentation of what is and is not included in a database backup.

## Safety
Never test destructive restore operations against the live shop database without a verified backup and a controlled recovery plan.
