# Phase 17 — Deferred Items & Guardrails

## Deferred
- WhatsApp customer communication.
- SMS and automated reminders.
- Email delivery.
- Scheduled exports.
- Cloud deployment.
- Cloud backup storage/automation.
- Payment gateways.
- GST automation.
- Double-entry accounting.
- Bank/cloud accounting integration.
- New payment/invoice types.
- Browser-accessible backup/restore.
- UI redesign.
- Generic file management.

## Guardrails
1. Exports use the authoritative Phase 14 report service.
2. React must not calculate authoritative totals.
3. Exports are read-only.
4. No user-supplied filesystem path is accepted.
5. No secrets are exported.
6. Do not implement WhatsApp in this phase.
7. Preserve Phase 16 backup/restore architecture.
8. No migration unless genuinely necessary.
9. Manual verification stays NOT STARTED until performed.
10. Avoid unrelated cleanup/refactoring.

## Definition of done
Implementation, automated tests, docs, and regression gates pass. Manual verification remains NOT STARTED until performed.
