# Saamu Tailors — Phase 4 API Specification

Base: `/api/v1/`

All endpoints require JWT authentication.

## Orders
- `GET /api/v1/orders/` — OWNER + STAFF; pagination, search by order/customer, status filtering and useful date filters.
- `GET /api/v1/orders/{id}/` — OWNER + STAFF.
- `POST /api/v1/orders/` — STAFF; existing customer, one or more garment items, valid measurements, initial NEW status.
- `PATCH /api/v1/orders/{id}/` — STAFF; only safe mutable fields.
- `POST /api/v1/orders/{id}/status/` — STAFF; body `{ "status": "CUTTING" }`; backend validates transitions.
- Cancellation may use the status endpoint or a dedicated action.

Never physically delete orders.

## Error format
Preserve the existing standardized format:
```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Human-readable message"
  }
}
```

## Permissions
| Operation | OWNER | STAFF |
|---|---:|---:|
| List | ✓ | ✓ |
| Detail | ✓ | ✓ |
| Create | ✗ | ✓ |
| Edit | ✗ | ✓ |
| Status change | ✗ | ✓ |
| Cancel | ✗ | ✓ |

Anonymous users remain denied.
