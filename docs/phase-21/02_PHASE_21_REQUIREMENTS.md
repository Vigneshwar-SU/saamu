# Phase 21 — Requirements

1. Inspect the current repository before modifying anything.
2. Preserve local Windows/PostgreSQL development behavior.
3. Production configuration must be environment-driven.
4. Secrets must never be committed, logged, returned by APIs, or embedded in frontend bundles.
5. DEBUG must be disabled in production.
6. Production host, CSRF, CORS, cookie, and security configuration must be explicit and testable.
7. Static, media, database backups, secrets, logs, and source code must remain clearly separated.
8. Application errors must not expose stack traces or sensitive configuration in production responses.
9. Health/readiness checks must remain safe and useful.
10. No destructive operation may be exposed through a browser endpoint.
11. No database schema change unless strictly required and explicitly justified.
12. Existing OWNER/STAFF RBAC must remain unchanged.
13. Existing Phase 16–20 functionality must remain compatible.
14. Add automated tests for every new production-hardening behavior.
15. Do not claim cloud deployment or live migration was performed.
16. Manual verification must remain NOT STARTED unless explicitly performed by the human operator.
17. Do not create a Git commit unless explicitly requested.
