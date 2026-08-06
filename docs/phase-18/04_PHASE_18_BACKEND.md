# Phase 18 — Backend Specification

## Message Builder
Implement a deterministic, independently testable service that:
- accepts authoritative customer/order/payment information;
- produces plain-text messages;
- handles missing optional fields cleanly;
- excludes internal notes and sensitive metadata;
- uses exact server-provided monetary values.

## Message Types
Use stable identifiers such as:
- `ORDER_ACKNOWLEDGEMENT`
- `ORDER_STATUS_UPDATE`
- `READY_FOR_COLLECTION`
- `PAYMENT_BALANCE`

Centralize template wording.

## Phone Normalization
- Strip harmless formatting.
- Reject empty/invalid values.
- Do not silently guess an ambiguous country code.
- Normalize to an international number only when the country context is unambiguous.
- Never log full phone numbers.

Do not create a duplicate phone field when the existing model already provides one.

## API
If needed, expose a read-only authenticated preparation endpoint under `/api/v1/communications/...`.

It may return only:
- message type;
- safe message text;
- normalized destination when available;
- optional WhatsApp URL.

No mutation or sending occurs.

Preserve existing 401/403/400/405 semantics and the standard error contract.

## Tests
Cover all message types, authoritative amounts, missing fields, phone validation, privacy exclusions, RBAC, read-only behavior, URL encoding, deterministic output, and secret leakage.
