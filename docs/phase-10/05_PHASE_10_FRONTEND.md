# Phase 10 — Frontend Specification

Follow the established vertical-slice pattern:

`types → services → hooks → dialogs/components → pages → routes`

## Salary / Payroll management
Enhance the existing Payroll experience to show:
- tailor
- salary model
- fixed salary
- completed pieces
- piece-rate earnings
- gross salary
- advances
- paid
- pending
- settlement status

## Salary configuration
STAFF can add/configure a tailor's salary model, fixed amount where required, effective date, and notes.

OWNER is read-only.

## Payroll detail
Show:
- salary model
- fixed component
- piece-rate component
- gross salary
- advance deduction
- paid
- pending
- attendance summary
- existing settlement controls

Reuse Phase 7 payment/settlement dialogs and hooks rather than duplicating them.

## UX
- Consistent money formatting.
- Server-derived values are authoritative.
- Finalized periods have no recalculation/edit controls.
- OWNER sees no mutation controls.
- Handle loading, empty, error, and pagination states consistently.
