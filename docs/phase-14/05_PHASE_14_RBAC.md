# Phase 14 — RBAC and Security

Backend authorization is authoritative.

## Anonymous
All reporting endpoints → 401.

## OWNER
Can view reports and apply filters.
Cannot mutate records through reports.

## STAFF
Can view reports and apply filters.
Reports do not grant additional mutation permissions.

## Financial Security
Do not expose or accept client-supplied authoritative:
- income totals
- expense totals
- net income
- payment totals
- refund totals
- payroll totals

Use existing backend services and permission checks.
