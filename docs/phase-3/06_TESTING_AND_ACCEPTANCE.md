# Phase 3 Testing and Acceptance

## Backend Tests

### Customer
- anonymous access rejected where appropriate
- OWNER can view
- STAFF can manage
- OWNER cannot create/update/archive
- STAFF can create/update/archive
- invalid/missing fields rejected
- valid mobile accepted
- search by name/mobile/ID where applicable
- pagination works
- archive retains data
- active/archived filtering works

### Measurements
- OWNER can view
- OWNER cannot modify
- STAFF can create/modify
- supported garment types work
- valid numeric measurements accepted
- invalid values rejected
- customer relationship enforced
- history preserved
- current measurement identifiable
- unrelated customer data cannot be accessed

## Frontend
Run:
- `npm run lint`
- `npx tsc --noEmit`
- `npm run build`

Manually verify:
1. OWNER login and customer view
2. OWNER mutation controls unavailable
3. STAFF login
4. STAFF create/edit/archive customer
5. STAFF create shirt measurement
6. STAFF create pant measurement
7. Measurement history remains visible
8. OWNER can view measurements but cannot modify
9. Loading/empty/error states work

## Integration
Verify:
Login → Customer API → Customer Detail → Measurement API → Update/History.

## Reporting
Create `docs/PHASE_3_COMPLETION_REPORT.md`.

For each command report:
```text
Command:
Result:
Status: PASS / FAIL / BLOCKED
```

Never claim unexecuted checks passed.
