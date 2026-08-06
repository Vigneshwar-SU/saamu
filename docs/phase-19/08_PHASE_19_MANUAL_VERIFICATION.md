# Phase 19 — Manual Verification

## Status
**NOT STARTED**

Automated tests do not count as manual verification.

### Reminder Discovery
- [ ] Start backend/frontend.
- [ ] Confirm eligible reminders appear.
- [ ] Confirm ineligible orders are excluded.

### Message Preparation
- [ ] Prepare each implemented reminder type.
- [ ] Confirm text matches current order/payment state.
- [ ] Confirm missing optional data is handled cleanly.

### WhatsApp Handoff
- [ ] Confirm the expected destination is opened.
- [ ] Confirm the UI does not claim delivery success.
- [ ] Confirm unavailable phone numbers disable the action safely.

### Duplicate Safety
- [ ] Repeat the same workflow and confirm documented idempotency behavior.

### RBAC
- [ ] Verify OWNER behavior.
- [ ] Verify STAFF behavior.
- [ ] Verify anonymous/unauthorized behavior where applicable.

### Regression
- [ ] Orders unchanged.
- [ ] Payments unchanged.
- [ ] Reports unchanged.
- [ ] Phase 18 communication workflow still works.
