# Phase 19 — Requirements

## Functional
- Define a small explicit set of operational reminder types only after repository inspection confirms the required data exists.
- Derive eligibility from authoritative existing models/services.
- Prepare messages using Phase 18 communication logic.
- Never send external messages automatically.
- Repeated evaluation must not create duplicate actionable reminders for the same unchanged event.
- Handle missing recipients, invalid state, and preparation failures explicitly.
- Do not duplicate customer phone, payment balance, or order-status fields.

## API
Any endpoint must use existing `/api/v1/` conventions, standard response/error envelopes, existing RBAC, strict validation, and no provider credentials.

## Frontend
If a UI is justified, include loading, empty, error/retry, and duplicate-action protection. The client must never calculate authoritative financial values.

## Acceptance
Focused tests plus all applicable backend/frontend regression gates must pass.
