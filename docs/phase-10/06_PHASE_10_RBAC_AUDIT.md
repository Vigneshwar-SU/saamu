# Phase 10 — RBAC & Audit

## Anonymous
Protected salary/payroll endpoints return `401`.

## OWNER
Can view salary configurations, salary components, payroll, attendance, advances, payments, and settlement information.

Cannot create/update salary configurations, calculate/finalize payroll, record advances/payments, or alter finalized payroll.

## STAFF
Can create salary configurations, perform allowed configuration mutations, calculate/finalize payroll, and use existing Phase 7 settlement mutations.

## Audit
Authenticated users are stored for applicable salary configuration mutations. Client-supplied audit fields must never be trusted.

## Immutability
No operation may alter finalized payroll values. Existing Phase 7 payment/advance audit trails remain unchanged.
