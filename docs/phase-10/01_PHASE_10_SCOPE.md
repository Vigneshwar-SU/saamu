# Phase 10 — Tailor Salary / Payroll

## Status
Planning / Implementation Specification

## Objective
Extend the existing Phase 6–7 attendance, payroll, advances, and settlement foundation into complete tailor salary management.

Salary models:
- `PER_GARMENT` — completed pieces × applicable piece-rate snapshot.
- `FIXED_SALARY` — fixed salary for the payroll period.
- `MIXED` — fixed salary + eligible piece-rate earnings.

## In scope
- Tailor salary-model configuration.
- Fixed salary amount configuration.
- Reuse of existing piece-rate configuration and snapshots.
- Fixed and mixed salary calculation.
- Integration with existing `PayrollPeriod` and `PayrollEntry`.
- Salary breakdown: fixed component, piece-rate component, gross salary, advances, paid, pending.
- Salary/payment history views.
- STAFF-only salary configuration/calculation mutations.
- OWNER read-only access.
- Backend validation, auditability, regression tests, frontend UI, and documentation.

## Existing functionality to preserve
Phase 6 already provides attendance and payroll periods/entries.
Phase 7 already provides advances, payments, settlement, immutability, and concurrency-safe settlement.

Phase 10 must extend these foundations, not duplicate or replace them.

## Out of scope
Tax/PF/ESI, leave, attendance monetary rules, bank/payment gateways, salary slips/PDFs, WhatsApp/SMS, double-entry accounting, GST, automatic income records, and changes to finalized payroll.

## Guardrails
- Finalized payroll remains immutable.
- Historical calculations remain reproducible.
- No negative payable values.
- Existing Phase 7 payment/advance logic remains authoritative.
