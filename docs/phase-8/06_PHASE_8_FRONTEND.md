# Phase 8 — Frontend Specification

Follow the established pattern:
`types → services → hooks → dialogs/components → pages → routes`

## Dashboard
Create a real dashboard with:
- date-range filter
- income card
- expense card
- net balance card
- payroll paid card
- salary advances card
- order status summary
- garment quantities
- tailor workload
- active customers/tailors
- recent income
- recent expenses

## Income
- paginated table
- date/category filters
- amount, description, reference, recorded-by, date
- STAFF-only Add Income

## Expenses
- paginated table
- date/category filters
- amount, description, reference, recorded-by, date
- STAFF-only Add Expense

Use React Hook Form + Zod as established.
OWNER must see no mutation controls.
Add Dashboard, Income and Expenses navigation without breaking existing modules.
