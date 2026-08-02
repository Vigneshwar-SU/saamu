# Saamu Tailors — Phase 4 Data Model

## Order
Suggested fields:
- id
- order_number (unique)
- customer FK
- order_date
- expected_delivery_date (nullable)
- status
- notes
- total/subtotal as appropriate using Decimal
- created_at
- updated_at
- collected_at (nullable)

## OrderItem
Suggested fields:
- id
- order FK
- garment_type
- quantity
- measurement version/reference and/or immutable snapshot
- unit_price/item amount
- notes
- created_at
- updated_at

## OrderStatusHistory
Recommended:
- order
- from_status
- to_status
- changed_by
- changed_at

## Constraints
Validate positive quantities, valid garment types, valid Decimal money, unique order number, valid customer, valid measurement version, valid dates and valid status transitions.

Create and apply Django migrations. Verify:
`python manage.py check`
`python manage.py migrate --check`
