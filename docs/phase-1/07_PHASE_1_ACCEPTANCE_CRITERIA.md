# Phase 1 Acceptance Criteria

Phase 1 is accepted only when the applicable criteria below are verified.

## Repository
- [ ] Clean project structure
- [ ] `docs/phase-0/` and `docs/phase-1/` correctly located
- [ ] No accidental duplicate documentation directory
- [ ] One backend Python virtual environment
- [ ] `.gitignore` protects secrets/generated files
- [ ] Git foundation safely established
- [ ] Existing valid work preserved

## Backend
- [ ] Django starts
- [ ] `python manage.py check` passes
- [ ] PostgreSQL is the only supported DB
- [ ] No SQLite fallback
- [ ] Environment configuration works
- [ ] DRF configured
- [ ] Default API permission is secure
- [ ] JWT foundation available
- [ ] CORS environment-driven
- [ ] `/api/v1/` namespace exists
- [ ] Health endpoint works
- [ ] Standard API error foundation exists
- [ ] Pagination configured
- [ ] Logging foundation exists
- [ ] Static/media configuration is clean
- [ ] No business models/endpoints introduced

## Frontend
- [ ] React starts
- [ ] TypeScript check passes
- [ ] Production build passes
- [ ] ESLint passes
- [ ] Centralized API client
- [ ] API URL environment-driven
- [ ] Frontend API error handling foundation
- [ ] Phase 0 UI identity preserved
- [ ] Routing foundation works
- [ ] No business workflows implemented

## Testing
- [ ] Backend test framework configured
- [ ] Health endpoint test exists and passes
- [ ] Useful foundation checks exist
- [ ] Verification commands actually executed
- [ ] Failures/blockers documented honestly

## Documentation
- [ ] README accurate
- [ ] Setup instructions reproducible
- [ ] Environment variables documented
- [ ] No real secrets documented
- [ ] No undocumented architectural changes

## Scope Protection
Do NOT implement:
- [ ] Customer CRUD
- [ ] Measurements
- [ ] Orders
- [ ] Garments
- [ ] Tailors
- [ ] Tailor workload
- [ ] Salary calculations
- [ ] Payments
- [ ] Income
- [ ] Expenses
- [ ] Locker/collection workflow
- [ ] Digital bills
- [ ] WhatsApp/SMS
- [ ] Business dashboard
- [ ] Reports
- [ ] Business notifications
- [ ] OWNER/STAFF business authorization

## Completion Report
Create:
```text
docs/PHASE_1_COMPLETION_REPORT.md
```

It must contain:
1. Summary
2. Repository Changes
3. Backend Changes
4. Frontend Changes
5. Security Changes
6. Testing
7. Verification Results
8. Commands Executed
9. Files Created/Modified
10. Known Issues
11. Deferred Items
12. Phase 2 Readiness

For every command:
```text
Command:
Result:
Status: PASS / FAIL / BLOCKED
```

## Stop Condition
After Phase 1, STOP. Do not start Phase 2 automatically. Phase 2 begins only after human review and approval.
