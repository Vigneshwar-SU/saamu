# Saamu Tailors — Phase 4 RBAC & Security

Backend authorization is authoritative.

## OWNER
Read-only. Verify 200 for reads and 403 for:
- POST create
- PATCH edit
- status transition
- cancellation

## STAFF
Can create, edit permitted fields, transition status and cancel where valid.

## Anonymous
All order endpoints must reject anonymous access.

## Data integrity tests
Cover invalid customer, missing/wrong measurement, quantity, amount, dates, duplicate order number, invalid transitions, terminal-state mutation and historical measurement immutability.

Never trust frontend role state or hidden controls for authorization.
