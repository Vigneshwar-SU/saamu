# Phase 2 Acceptance Criteria

## User Model
- [ ] User has application role.
- [ ] Exactly OWNER and STAFF exist.
- [ ] Role choices are explicit.
- [ ] Existing custom User/migrations remain intact.
- [ ] No unnecessary third role.

## Backend Authentication
- [ ] Login exists.
- [ ] OWNER login succeeds.
- [ ] STAFF login succeeds.
- [ ] Invalid credentials fail safely.
- [ ] Refresh works.
- [ ] `/api/v1/auth/me/` works.
- [ ] `/me/` returns role.
- [ ] Sensitive fields are absent.
- [ ] Logout exists.
- [ ] Logout invalidates authentication as designed.

## Authorization
- [ ] Reusable role permission mechanism exists.
- [ ] OWNER is view-only for business operations.
- [ ] STAFF is the operational role.
- [ ] Backend does not trust frontend role values.
- [ ] Django `is_staff` is not incorrectly treated as application STAFF.
- [ ] Superuser behavior is documented.

## Frontend
- [ ] Login uses real backend.
- [ ] Mock login/navigation removed.
- [ ] Central auth state exists.
- [ ] User and role available.
- [ ] Bearer token attached centrally.
- [ ] Refresh works.
- [ ] Failed refresh clears session.
- [ ] Logout clears local state.
- [ ] Protected routes redirect anonymous users.
- [ ] Login/loading/error states work.
- [ ] Role-aware navigation foundation exists.

## Security
- [ ] No plaintext passwords.
- [ ] No secrets committed.
- [ ] No tokens logged.
- [ ] Invalid login does not reveal account existence.
- [ ] CORS remains restricted.
- [ ] JWT configuration remains centralized.
- [ ] Frontend role tampering is ineffective.

## Tests
- [ ] Backend tests pass.
- [ ] Authentication tests pass.
- [ ] Authorization tests pass.
- [ ] Frontend lint passes.
- [ ] TypeScript check passes.
- [ ] Frontend build passes.
- [ ] Integration flow verified.

## Scope Protection
Do NOT implement:
- [ ] Customer management
- [ ] Measurements
- [ ] Orders
- [ ] Garments
- [ ] Tailor management
- [ ] Workload
- [ ] Salary
- [ ] Payments
- [ ] Income
- [ ] Expenses
- [ ] Locker management
- [ ] Collection workflow
- [ ] Digital bills
- [ ] WhatsApp/SMS
- [ ] Business dashboard
- [ ] Reports
- [ ] Notifications

## Completion Report
Create:
```text
docs/PHASE_2_COMPLETION_REPORT.md
```

Include:
1. Summary
2. User Model Changes
3. Backend Authentication
4. Authorization/Roles
5. Frontend Authentication
6. Security
7. Tests
8. Verification Results
9. Commands Executed
10. Files Created/Modified
11. Known Issues
12. Deferred Items
13. Phase 3 Readiness

For each command:
```text
Command:
Result:
Status: PASS / FAIL / BLOCKED
```

## Stop Condition
After Phase 2, STOP. Do not start Phase 3 automatically. Wait for human review and approval.
