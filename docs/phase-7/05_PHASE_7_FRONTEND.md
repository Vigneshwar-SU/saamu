# Phase 7 — Frontend Specification

Follow the established pattern:
types → services → hooks → dialogs/components → pages → routes.

## Payroll
Enhance payroll list/detail with:
- settlement status
- gross payable
- advances
- paid amount
- outstanding amount

## Payroll Detail
For each tailor show:
- Gross payable
- Advance deduction
- Paid
- Outstanding
- Settlement status
- Payment history
- STAFF-only Record Payment
- STAFF-only Apply Advance

OWNER sees all information but no mutation controls.

## Advances Page
Provide:
- tailor filter
- status filter
- date range
- pagination
- amount
- date
- status
- notes
- recorded by
- STAFF-only Add Advance

## Payment Dialog
Fields:
- amount
- payment date
- payment method
- reference
- notes

Display gross payable, paid, advance deductions, current outstanding, and maximum payable.

Backend validation remains authoritative.

## UX
Reuse existing MUI/theme patterns, confirmation dialogs, feedback states, and natural page scrolling. Avoid viewport-height nested scroll containers.
