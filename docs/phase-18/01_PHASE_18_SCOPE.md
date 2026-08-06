# Phase 18 — Scope
## Title
Customer Communication & WhatsApp-Ready Delivery

## Objective
Extend Saamu Tailors with a controlled customer-communication workflow built around WhatsApp, while preserving existing order, customer, billing, payment, and reporting behavior.

## Approved Scope
- Customer communication from relevant customer/order surfaces.
- WhatsApp-ready message generation for order acknowledgement, status update, ready-for-collection, and payment/balance summary.
- Reusable server-authoritative message templates.
- Copy-message and Open WhatsApp actions; no automated WhatsApp sending.
- Safe phone-number normalization and WhatsApp handoff URL generation.
- Frontend loading, error, and duplicate-action protection.
- Backend tests, frontend checks, documentation, and manual verification checklist.

## Explicit Boundary
No WhatsApp Business API, Meta Cloud API, Twilio, or paid messaging-provider integration.

## Non-Goals
No new payment types, GST, accounting, cloud deployment, scheduled reminders, report redesign, backup/restore redesign, or unrelated UI work.
