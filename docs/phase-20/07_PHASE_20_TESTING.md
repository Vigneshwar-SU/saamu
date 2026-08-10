# Phase 20 — Testing Specification

## Backend Gates
Run:
- python manage.py check
- python manage.py makemigrations --check --dry-run
- focused Phase 20 tests
- full backend test suite
- Black check
- isort check

## Required Test Coverage
- Local database configuration remains valid.
- Environment-provided database settings are interpreted correctly.
- Missing required production configuration is rejected when production validation is enabled.
- Invalid configuration produces safe errors.
- Passwords/secrets never appear in errors.
- No business data is mutated by configuration/readiness behavior.
- Existing backup/restore functionality remains unaffected.
- Any optional readiness endpoint obeys authentication and GET-only semantics.

## Frontend Gates
If frontend changed:
- npm run lint
- npx tsc --noEmit
- npm run build

If frontend is unchanged, run relevant regression checks if practical.

## Migration Safety
A schema migration is not expected. If one appears, STOP and inspect why before proceeding.
