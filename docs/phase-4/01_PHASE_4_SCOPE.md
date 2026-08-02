# Saamu Tailors — Phase 4: Orders & Tailoring Workflow

## Goal
Build the real Order Management workflow on top of the completed Customer + Measurement foundation.

## In scope
- Order creation linked to an existing customer
- Human-friendly unique order number
- Order date and expected delivery date
- Order status lifecycle
- SHIRT/PANT garment items
- Quantity per item
- Measurement version/snapshot used by the order
- Order/item notes
- Basic Decimal pricing fields for future billing
- Order list, search, filters, pagination
- Order detail
- STAFF create/edit/status/cancel operations
- OWNER read-only access
- Status/timestamps/history
- Django REST API + React UI
- Tests, documentation and Git commit/push after approval

## Explicitly out of scope
Tailors/workload, salary, income/expenses, payments, digital bills, WhatsApp/SMS, dashboard/reporting, locker inventory, notifications, cloud deployment, multi-branch support, customer deletion and measurement-diff UI.

## Business workflow
1. Customer arrives with cloth.
2. Staff identifies the existing customer.
3. Staff creates an order.
4. Garment items and measurements are recorded.
5. Order progresses through tailoring.
6. Finished order becomes READY.
7. Customer collects it.
8. Later phases connect orders to workload, payments, bills and notifications.
