# Phase 16 — Local to Cloud PostgreSQL Migration

## Goal
Move Saamu Tailors from the current local PostgreSQL installation to a future hosted PostgreSQL instance without changing business-data semantics.

## Current local architecture
Application → PostgreSQL

## Target architecture
Application → Hosted PostgreSQL

The Django application should continue using the same database abstraction and models.

## Migration outline
1. Freeze or minimize writes.
2. Create and verify a fresh PostgreSQL backup.
3. Provision the target PostgreSQL database.
4. Apply compatible database configuration/environment variables.
5. Restore the PostgreSQL backup into the target.
6. Run schema/application checks.
7. Verify representative business records:
   - users
   - customers
   - orders
   - invoices
   - customer payments/refunds
   - expenses
   - payroll
   - salary advances
8. Point the application to the target database.
9. Run smoke tests.
10. Keep the original local database and pre-migration backup until the cloud environment is proven stable.

## Important separation
Database migration does not automatically migrate:
- media/uploads
- static files/build output
- `.env`/secrets
- logs
- source code

Those require separate deployment/migration procedures.

## Future cloud phase
Cloud storage, automated backups, deployment, HTTPS, monitoring, and production hosting are explicitly outside Phase 16.
