# Phase 11 — Testing Strategy

## Backend
Run:
- Django system checks.
- Migration checks.
- Phase 11 tests.
- Full regression suite.
- Formatting/import checks already used by the repository.

## Test Coverage
Cover:
- anonymous access
- OWNER read access
- OWNER mutation rejection
- STAFF payment creation
- each supported payment type
- invalid payment values
- refund behavior
- order total calculation
- total paid calculation
- outstanding balance
- payment status
- payment history
- bill data endpoint/response
- authorization boundaries
- regression against existing Phase 7 settlement behavior

## Frontend
Run the project's existing:
- lint
- TypeScript check
- production build

Verify the affected pages/components compile and integrate with the backend.

## Regression
All previously passing tests must remain passing.
