# Phase 21 — Frontend Specification

## Objective
Prepare the React frontend for production deployment without adding business features.

## Requirements
- No secrets or private backend credentials in frontend source or build output.
- API base URL must be deployment-configurable through the existing frontend configuration mechanism.
- Do not hard-code localhost as the only API target.
- Production build must succeed.
- Existing authentication and API behavior must remain intact.
- Existing reports exports, communication panel, reminders, and all prior pages must remain functional.

## Error Handling
Production-facing API errors should be rendered through the existing safe error mechanisms. Do not expose backend stack traces or internal configuration.

## Out of Scope
- UI redesign.
- New business pages.
- Cloud-specific SDKs.
- Client-side database access.
