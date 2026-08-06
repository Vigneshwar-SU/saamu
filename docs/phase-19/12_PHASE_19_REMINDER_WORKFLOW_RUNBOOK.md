# Phase 19 — Reminder Workflow Runbook

## Purpose
Operational guidance for the reminder preparation/review workflow after implementation.

## Flow
1. Identify eligible reminders.
2. Review order/customer context.
3. Prepare the server-authored message.
4. Review the preview.
5. Use the Phase 18 WhatsApp handoff when a usable number exists.
6. Treat actual delivery as external unless a future provider integration establishes delivery status.
7. Re-evaluate after material order/payment/status changes.

## Safety
Never paste credentials into the application, treat `wa.me` as delivery confirmation, alter financial values to fit a reminder, or force a reminder through inconsistent business state.

## Troubleshooting
- No reminder: verify eligibility and order status.
- No WhatsApp action: verify the existing customer mobile number.
- Incorrect balance: inspect the authoritative payment summary.
- Duplicate: inspect documented idempotency behavior.
