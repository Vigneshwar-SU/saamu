# Phase 21 — Smoke Test & Rollback Specification

## Smoke Test

### Application
- [ ] Health endpoint responds correctly.
- [ ] Login works.
- [ ] OWNER permissions remain view-only where defined.
- [ ] STAFF management workflows work.

### Business
- [ ] Customer creation/viewing.
- [ ] Order creation and lifecycle.
- [ ] Measurements.
- [ ] Tailor assignment/workload.
- [ ] Payments/billing.
- [ ] Finance/reports.
- [ ] CSV/PDF exports.
- [ ] Communication preparation.
- [ ] Reminder review.

### Operational
- [ ] PostgreSQL connectivity.
- [ ] Static assets load.
- [ ] Media behavior is correct.
- [ ] Logs are generated without secrets.
- [ ] Error responses do not expose stack traces.

## Rollback

Rollback must distinguish:
- application rollback;
- configuration rollback;
- database rollback.

### Application Rollback
Deploy the previously known-good application artifact.

### Configuration Rollback
Restore the previously known-good environment configuration without committing secrets.

### Database Rollback
Only perform database restoration when data corruption/loss requires it. Use the Phase 16 safety-backup and restore procedure. Never treat an application rollback as permission to overwrite the database.

## Success Criteria
A rollback is complete only after:
- application starts;
- health check passes;
- database is reachable;
- authentication works;
- critical business flow smoke tests pass.
