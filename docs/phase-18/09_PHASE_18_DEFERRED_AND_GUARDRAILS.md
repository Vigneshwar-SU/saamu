# Phase 18 — Deferred & Guardrails

## Deferred
- WhatsApp Business / Meta Cloud API integration.
- Automated sending.
- Scheduled reminders.
- Background messaging workers.
- Delivery/read receipts.
- Message history/audit log.
- SMS/email providers.
- Cloud deployment.
- Cloud backup automation.
- New payment/invoice types.
- GST automation.
- Double-entry accounting.
- UI redesign.
- Generic communication/file management.

## Guardrails
1. Never send WhatsApp messages automatically.
2. Never add provider credentials for a future integration.
3. Never expose generic URL/command execution.
4. Never let the frontend invent financial totals/balances.
5. Never include private/internal notes.
6. Never log full phone numbers unnecessarily.
7. Never alter order/payment semantics to simplify messaging.
8. Do not add migrations without a concrete requirement.
9. Do not mark manual verification complete from automated tests.
10. Do not create a commit unless explicitly requested.
