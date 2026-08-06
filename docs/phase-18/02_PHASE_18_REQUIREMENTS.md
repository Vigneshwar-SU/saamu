# Phase 18 — Requirements

## Functional Requirements
### R1 — Server-authoritative messages
Customer/order/payment facts used in messages must come from backend-authoritative data. The frontend must not calculate balances or totals.

### R2 — Supported templates
Provide reusable templates for:
- Order acknowledgement
- Order status update
- Ready for collection
- Payment / balance summary

### R3 — Safe customer targeting
Use the customer's stored mobile number. If no usable number exists, Open WhatsApp must be unavailable with a clear explanation.

### R4 — WhatsApp handoff
Open WhatsApp using a fixed handoff URL with normalized destination and URL-encoded message. Never claim delivery or sending occurred.

### R5 — Copy fallback
Every supported communication flow must provide a copy-to-clipboard fallback.

### R6 — No automatic sending
No server-side dispatch, background worker, webhook, provider credential, or automatic customer contact.

### R7 — RBAC
Existing OWNER/STAFF authorization remains authoritative.

### R8 — Privacy
Include only information necessary for the selected communication purpose. Never include internal notes, audit metadata, credentials, or unrelated information.

### R9 — Duplicate-action protection
Communication actions must prevent accidental repeated operations.

### R10 — Error handling
Missing data, invalid phones, failed requests, clipboard failure, and malformed responses must produce recoverable errors.

## Non-Functional Requirements
- No migration unless objectively required.
- Preserve the existing API error contract.
- Keep message generation deterministic and testable.
- No secrets in frontend code.
- No WhatsApp provider credentials.
