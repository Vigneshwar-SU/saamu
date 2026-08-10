# Phase 20 — Requirements

1. Existing local PostgreSQL behavior must remain supported.
2. Database connection settings must be environment-driven.
3. No database credentials may be committed or exposed in logs/errors.
4. No local absolute path may be required for the application to start.
5. Backup/restore remains the authoritative portability mechanism.
6. Migration preparation must be repeatable and non-destructive.
7. The application must fail clearly when required production configuration is invalid.
8. Development-friendly defaults may remain where they do not weaken explicit production validation.
9. Media/uploads and static assets must be documented separately from PostgreSQL data.
10. The cloud migration procedure must include final backup, transfer, restore, verification, smoke test, rollback/return-to-local guidance, and retention of the original local environment.
11. No browser endpoint may perform database migration, arbitrary command execution, or destructive restore.
12. Existing OWNER/STAFF behavior and API contracts must remain unchanged.
13. No migration should be introduced unless repository inspection proves one is necessary.
14. Automated tests must cover every new configuration/validation behavior.
15. Manual verification must remain NOT STARTED until a human executes the checklist.
