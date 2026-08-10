# Phase 22 — API Contract

Use the existing Settings/ShopDetails API if one already exists. Do not introduce a duplicate endpoint merely for the Settings page.

## Operations
- Read current shop/business configuration.
- Update only fields allowed by the established permission model.

## Responses
Return persisted authoritative values using existing response conventions. Never expose sensitive configuration.

Validation, authentication and authorization errors must follow the existing DRF conventions.

Frontend TypeScript types must accurately match the real API. Do not use `any` to bypass mismatches.
