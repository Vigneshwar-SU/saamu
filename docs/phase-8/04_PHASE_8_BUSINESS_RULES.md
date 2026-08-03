# Phase 8 — Business Rules

1. Income amount must be greater than zero.
2. Expense amount must be greater than zero.
3. Category and date are required.
4. `date_from` and `date_to` are inclusive.
5. `date_to` cannot precede `date_from`.
6. Recorded income = sum of Phase 8 income records in the range.
7. Recorded expenses = sum of Phase 8 expense records in the range.
8. Net recorded balance = income - expenses.
9. Payroll paid is derived from actual `PayrollPayment.amount` records.
10. Salary advances must remain a separate metric; do not silently classify them as expenses.
11. Order revenue must be clearly distinguished from recorded cash income.
12. Finalized payroll, payment history and advance history must not be rewritten.
13. Dashboard is read-only and must never mutate source data.
