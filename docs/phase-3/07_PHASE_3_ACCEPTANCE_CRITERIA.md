# Phase 3 Acceptance Criteria

## Customer
- [ ] Customer model exists with stable ID
- [ ] Name and mobile exist
- [ ] Practical optional contact/address/notes fields
- [ ] Active/archive state
- [ ] created_at and updated_at
- [ ] Safe migration

## Customer API
- [ ] List/detail work
- [ ] STAFF create/update/archive
- [ ] OWNER view only
- [ ] Pagination
- [ ] Search
- [ ] Filtering
- [ ] Validation
- [ ] Standardized errors

## Measurements
- [ ] Measurement model exists
- [ ] Customer relationship
- [ ] Shirt support
- [ ] Pant support
- [ ] Structured numeric values
- [ ] Unit documented
- [ ] Current measurement identifiable
- [ ] History preserved
- [ ] STAFF create/modify
- [ ] OWNER view only
- [ ] Invalid values rejected

## Frontend
- [ ] Customer placeholder replaced
- [ ] List/search/pagination
- [ ] STAFF create/edit/archive
- [ ] Detail
- [ ] Current measurements
- [ ] Measurement history
- [ ] Shirt measurement UI
- [ ] Pant measurement UI
- [ ] OWNER view-only UI
- [ ] STAFF management controls
- [ ] Loading/empty/error states

## Security & Quality
- [ ] Backend enforces OWNER read-only
- [ ] No anonymous customer access
- [ ] Customer relationships authorized
- [ ] No unnecessary sensitive data exposure
- [ ] Backend tests pass
- [ ] Frontend lint passes
- [ ] TypeScript passes
- [ ] Build passes
- [ ] Phase 1/2 tests remain passing
- [ ] No unrelated business features implemented

## Out of Scope
Do NOT implement Orders, Garments, cloth inventory, Tailors, workload, salary, income, expenses, payments, locker/collection workflow, digital bills, WhatsApp/SMS, dashboard/reporting, or notifications.

## Completion Report
Create `docs/PHASE_3_COMPLETION_REPORT.md` with:
1. Summary
2. Customer Model
3. Customer APIs
4. Measurement Model
5. Measurement APIs
6. Permissions
7. Frontend
8. Tests
9. Verification Results
10. Commands Executed
11. Files Created/Modified
12. Known Issues
13. Deferred Items
14. Phase 4 Readiness

Use PASS/FAIL/BLOCKED honestly.

## Stop Condition
After Phase 3, STOP. Do not start Phase 4 automatically.
