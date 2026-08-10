# Phase 21 — Manual Verification

**Status: NOT STARTED**

Automated tests do not count as manual verification.

## Local Regression
- [ ] Start backend using existing local configuration.
- [ ] Start frontend.
- [ ] Login as OWNER.
- [ ] Login as STAFF.
- [ ] Verify existing core workflows remain usable.

## Production Configuration
- [ ] Review production environment variables without exposing secrets.
- [ ] Confirm DEBUG is disabled.
- [ ] Confirm allowed hosts are correct.
- [ ] Confirm CSRF/CORS origins are correct.
- [ ] Confirm secure cookie/HTTPS settings match deployment topology.
- [ ] Confirm production startup/check behavior with intentionally invalid configuration.

## Health
- [ ] Verify `/api/v1/health/` returns the expected safe readiness response.
- [ ] Confirm no credentials or sensitive filesystem information are exposed.

## Existing Features
- [ ] Reports page and CSV/PDF exports.
- [ ] Order communication panel.
- [ ] Reminders page.
- [ ] Backup/restore operator commands.
- [ ] Authentication and RBAC.

## Deployment Readiness
- [ ] Build frontend production assets.
- [ ] Review static/media boundaries.
- [ ] Review logs and error behavior.
- [ ] Review rollback procedure.

## Important
Do not perform a live cloud migration as part of Phase 21. That belongs to the dedicated migration phase.
