# Phase 14 — Database Specification

Prefer existing tables and relationships:
- Order and OrderItem
- Customer
- Tailor / WorkAssignment
- CustomerPayment
- Expense
- Payroll-related records where already available

Do not create a reporting database or duplicated aggregate tables.

Calculated values should be derived server-side.

No migration is expected unless a genuinely necessary schema requirement is discovered.

If no schema change is required:
`python manage.py makemigrations --check --dry-run`
must report no changes detected.

Do not alter historical financial records.
