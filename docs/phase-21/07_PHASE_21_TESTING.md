# Phase 21 — Testing Specification

## Backend Gates
Run:
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused Phase 21 tests
- full backend test suite
- Black check
- isort check

## Frontend Gates
Run:
- `npm run lint`
- `npx tsc --noEmit`
- `npm run build`

## Required Test Areas
- development configuration remains valid;
- production configuration validation;
- unsafe secret rejection;
- host/CSRF/CORS validation;
- secure-cookie/security setting behavior;
- safe logging/error behavior;
- API health safety;
- no secret leakage;
- frontend API configuration;
- regression compatibility with Phases 16–20.

## Test Isolation
Tests must not:
- contact real cloud infrastructure;
- migrate the live shop database;
- send WhatsApp/SMS/email;
- expose real credentials;
- alter real production data.

## Completion Standard
All focused and full regression gates must pass before Phase 21 is reported PASS.
