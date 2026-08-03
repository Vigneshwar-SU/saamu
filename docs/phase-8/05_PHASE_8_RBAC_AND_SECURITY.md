# Phase 8 — RBAC & Security

## OWNER
Read:
- income
- expenses
- dashboard

Mutation:
- income create → 403
- expense create → 403

## STAFF
Can create income and expenses and read all Phase 8 data.

## Anonymous
All Phase 8 endpoints → 401.

## Security
- Backend permissions are authoritative.
- Never accept `recorded_by` from the client.
- Store authenticated recorder and timestamps.
- Historical records have no physical delete API.
