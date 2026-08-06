# Phase 19 — API Specification

Use existing `/api/v1/` conventions and the standard success/error contract.

Potential endpoint shapes are planning candidates only and must be validated against the repository before implementation:
- `GET /api/v1/communications/reminders/`
- `GET /api/v1/communications/reminders/<id>/prepare/`

Rules:
- Anonymous → 401.
- Unauthorized role → 403.
- Invalid resource → 404.
- Invalid parameters/state → 400 validation_error.
- Unsupported methods → 405.
- No provider calls, secrets, or full phone numbers in logs.

Avoid mutation endpoints when a read-only derived workflow is sufficient.
