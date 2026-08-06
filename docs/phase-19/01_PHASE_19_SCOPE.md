# Phase 19 — Scope

## Objective
Extend the Phase 18 WhatsApp-ready communication foundation into a safe, auditable reminder workflow without automatic external sending.

## In Scope
- Operational reminder definitions based on existing order/payment lifecycle data.
- Deterministic eligibility evaluation.
- Reminder preparation using the Phase 18 communication foundation.
- Operator review of pending reminders.
- Duplicate-prevention/idempotency rules.
- Explicit reminder status and failure handling.
- Automated tests and documentation.

## Out of Scope
- Automatic WhatsApp/Meta/Twilio/SMS/email sending.
- Provider credentials, webhooks, external background senders, or cloud schedulers.
- Cloud deployment/backup automation.
- New payment/invoice types.
- Unrelated UI redesign.

## Rules
1. Existing business rules remain authoritative.
2. Reuse existing payment, order, customer, and communication logic.
3. Preserve OWNER/STAFF RBAC.
4. Never log full phone numbers or message contents unnecessarily.
5. Never claim a WhatsApp handoff means delivery.
6. Do not add a migration unless genuinely required and justified.
7. Manual verification remains NOT STARTED until a human performs it.
