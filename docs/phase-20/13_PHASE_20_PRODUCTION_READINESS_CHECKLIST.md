# Phase 20 — Production Readiness Checklist

## Configuration
- [ ] Database settings are environment-driven.
- [ ] No secret is committed.
- [ ] No local absolute path is required.
- [ ] Production validation is explicit.

## Database
- [ ] PostgreSQL target is compatible.
- [ ] Final backup created.
- [ ] Backup integrity verified.
- [ ] Restore tested in disposable/non-production target.
- [ ] Representative records verified.

## Application
- [ ] Backend checks pass.
- [ ] Full backend tests pass.
- [ ] Frontend checks pass.
- [ ] OWNER login works.
- [ ] STAFF login works.
- [ ] Reports/export works.
- [ ] Reminder review works.
- [ ] WhatsApp-ready preparation remains preparation-only.

## Operational Safety
- [ ] Original local database retained.
- [ ] Rollback path documented.
- [ ] Credentials protected.
- [ ] Backup is not publicly served.
- [ ] No browser destructive database controls exist.

## Human Sign-Off
Phase 20 is not considered live cloud deployment merely because configuration is implemented. A human must execute the manual checklist before claiming production migration success.
