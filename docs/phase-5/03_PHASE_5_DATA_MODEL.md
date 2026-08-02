# Saamu Tailors — Phase 5 Data Model

## Tailor
Suggested fields:
- id
- full_name
- mobile_number (optional)
- notes
- is_active
- created_at
- updated_at

Use a stable internal ID.

## PieceRate
Suggested fields:
- id
- garment_type
- rate_per_piece
- is_active
- created_at
- updated_at

Use Decimal, never float.

## WorkAssignment
Suggested fields:
- id
- tailor
- order_item
- assigned_quantity
- completed_quantity
- status
- rate_per_piece_snapshot
- assigned_at
- started_at (nullable)
- completed_at (nullable)
- created_by
- updated_at

The historical rate snapshot is mandatory.

## Relationships
```text
Customer
   │
   └── Order
        │
        └── OrderItem
              │
              └── WorkAssignment ─── Tailor
                         │
                         └── PieceRate snapshot
```

## Constraints
- assigned_quantity >= 1
- completed_quantity >= 0
- completed_quantity <= assigned_quantity
- rate_per_piece_snapshot >= 0
- active tailor required for new assignment
- valid order item required
- historical records remain queryable after tailor archival

Keep the first implementation simple and consistent with the existing Django architecture.
