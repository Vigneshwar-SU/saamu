# Phase 8 — Data Model

## Income
Fields:
- `category`
- `amount`
- `income_date`
- `description`
- `reference`
- `recorded_by`
- `created_at`
- `updated_at`

Rules:
- amount > 0
- category/date required
- no delete endpoint
- authenticated user supplies `recorded_by` server-side

## Expense
Fields:
- `category`
- `amount`
- `expense_date`
- `description`
- `reference`
- `recorded_by`
- `created_at`
- `updated_at`

Rules:
- amount > 0
- category/date required
- no delete endpoint
- authenticated user supplies `recorded_by` server-side

## Initial Categories

Income:
- `ORDER_PAYMENT`
- `OTHER_INCOME`

Expense:
- `RENT`
- `ELECTRICITY`
- `MATERIAL`
- `MAINTENANCE`
- `SHOP_SUPPLIES`
- `TRANSPORT`
- `OTHER_EXPENSE`

## Dashboard Derived Metrics
- recorded income
- recorded expenses
- net recorded balance
- payroll payments
- salary advances as a separate metric
- order counts/statuses
- garment quantities
- active tailor/customer counts
- assigned/completed/outstanding workload
- recent income/expenses

Use Decimal for all monetary calculations.
