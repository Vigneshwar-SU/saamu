# Payments — Automated Verification Checklist

## Backend
- [ ] Django system check passes
- [ ] No missing migrations
- [ ] Payment model/API tests pass
- [ ] RBAC tests pass
- [ ] ADVANCE tests pass
- [ ] PARTIAL tests pass
- [ ] FINAL tests pass
- [ ] REFUND tests pass
- [ ] Order total / net paid / outstanding tests pass
- [ ] Full backend suite passes

## Frontend
- [ ] TypeScript check passes
- [ ] ESLint passes
- [ ] Production build passes
- [ ] Payment API integration is type-safe

## Integration
- [ ] Payments update applicable order/invoice state
- [ ] Income reflects applicable payments
- [ ] Dashboard financial summaries remain correct
- [ ] OWNER cannot mutate payments
- [ ] STAFF can perform permitted operations

## Manual Verification
- [ ] Full manual Payments verification
- [ ] Cross-module business-flow verification
- [ ] Owner/staff UI verification

Manual verification is intentionally deferred until the project owner is well.
