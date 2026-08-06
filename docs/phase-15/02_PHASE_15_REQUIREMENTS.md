# Phase 15 — Requirements

1. Existing Version 1 features must continue working unchanged.
2. Django/DRF remains authoritative for validation, permissions and financial calculations.
3. No client-side arithmetic may become authoritative.
4. OWNER remains read-only where defined; STAFF retains management permissions.
5. Anonymous users must not access protected APIs/pages.
6. API failures must use the project's standard error contract.
7. Frontend failures must show understandable feedback instead of blank/broken screens.
8. Local PostgreSQL data must have a documented backup and restore procedure.
9. Production configuration must not depend on development-only behavior.
10. No unnecessary schema changes may be introduced.
11. Existing tests must remain green.
