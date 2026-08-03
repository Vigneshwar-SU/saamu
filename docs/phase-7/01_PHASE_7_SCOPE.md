# Phase 7 — Salary Payments, Advances & Payroll Settlement

## Purpose
Extend the Phase 6 payroll foundation into actual salary settlement without modifying finalized payroll calculations.

## In Scope
- Salary advances linked to tailors.
- Payroll payments linked to finalized payroll entries.
- Partial and full settlement.
- Advance deductions.
- Payment methods and references.
- Outstanding payable calculation.
- Payment/settlement history and audit trail.
- OWNER read-only; STAFF mutation access.
- Frontend for advances and payroll settlement.
- Validation preventing overpayment.
- Regression safety for Phases 1–6.

## Out of Scope
- Tax/PF/ESI.
- Leave management.
- Notifications/WhatsApp/SMS.
- Dashboard analytics.
- Income/expense accounting.
- Customer billing/invoices.
- Bank/payment-gateway integrations.
- Changes to finalized payroll calculations.

## Core Guardrail
Finalized payroll is immutable. Phase 7 records settlement against payroll; it does not rewrite payroll earnings.
