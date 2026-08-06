# Phase 18 — Manual Verification Checklist

**Status: NOT STARTED**

A human must perform these checks in the running application before marking them complete.

## Customer Communication
- [ ] Open a customer with a valid mobile number.
- [ ] Prepare each supported message.
- [ ] Verify message preview.
- [ ] Copy and verify pasted content.
- [ ] Open WhatsApp and verify destination/message.
- [ ] Confirm the app does not claim the message was sent.

## Order Flows
- [ ] Order acknowledgement uses correct data.
- [ ] Status update reflects current status.
- [ ] Ready-for-collection message is correct.
- [ ] Payment/balance message matches authoritative values.

## Invalid/Missing Phone
- [ ] Customer without phone.
- [ ] Malformed phone.
- [ ] Open WhatsApp is unavailable with a clear explanation.
- [ ] Copy fallback behaves correctly.

## Permissions
- [ ] OWNER behavior verified.
- [ ] STAFF behavior verified.
- [ ] Anonymous/unauthorized access rejected.

## Error/Duplicate Actions
- [ ] Clipboard/API failure is recoverable.
- [ ] Retry works.
- [ ] Rapid repeated clicks do not cause duplicate actions/windows.

## Privacy
- [ ] Internal notes absent.
- [ ] Unrelated customer data absent.
- [ ] No credentials/secrets exposed.

## Regression
- [ ] Existing customer/order/payment flows work.
- [ ] Reports/export work.
- [ ] Backup/restore commands remain available.
