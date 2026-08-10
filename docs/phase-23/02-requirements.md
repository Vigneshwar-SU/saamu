# Phase 22 — Requirements

## Existing Functionality Audit
Before coding, inspect existing Settings routes/components, `ShopDetails`, billing APIs, serializers, views, permissions, tests, and frontend patterns.

Do not create a second source of truth for shop information.

## Shop / Business Information
Expose only fields already supported by the current domain model, such as:
- Shop/business name
- Address
- Contact phone
- Other existing business information

## Account Information
Show appropriate current-user information already supported by the application. Do not expose or alter authorization/security properties unless explicitly supported.

## Preferences
Implement only preferences that have real backend/domain meaning. Avoid speculative settings.

## Permissions
Backend authorization is authoritative.
- OWNER: follow the project's established read-only behavior.
- STAFF: allow management only where the existing permission model permits it.
- Never rely only on frontend hiding/disabling.

## UX
Provide clear sections, loaded values, validation, save feedback, loading/error states, retry behavior, and sensible unsaved-change protection.

## Integration
Changes must propagate through the same authoritative data consumed by billing/invoices and other modules.

## Security
Never expose database passwords, JWT secrets, Django secret key, environment variables, API credentials, or deployment configuration.
