# Phase 6 — Attendance & Payroll Foundation

## Goal
Introduce tailor attendance and a practical payroll foundation while preserving the Phase 5 workload and piece-rate contracts.

## In Scope
- Tailor attendance: PRESENT, ABSENT, HALF_DAY.
- Daily attendance creation, editing, filtering and review.
- Payroll periods with DRAFT → CALCULATED → FINALIZED lifecycle.
- Payroll calculation from completed piece-rate work.
- Tailor payroll summaries and assignment-level earning breakdowns.
- OWNER read-only / STAFF mutation RBAC.
- Frontend Attendance and Payroll pages.
- Automated tests, manual verification, documentation and Git push.

## Out of Scope
Fixed salary rules, overtime, leave, bonuses, advances, tax/PF/ESI, salary transfers, bank/UPI integration, payslips, WhatsApp/SMS, income/expense, payments, billing and dashboard analytics.

## Critical Rules
- Historical WorkAssignment.rate_per_piece_snapshot is authoritative for payroll.
- Outstanding/in-progress pieces never count as earnings.
- Missing attendance is not automatically PRESENT.
- Do not invent a fixed salary or daily wage rule.
- FINALIZED payroll must not be silently recalculated or mutated.
