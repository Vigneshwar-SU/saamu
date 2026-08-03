# Phase 9 — API Specification

All endpoints are under `/api/v1/`.

## Invoices

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET / POST | `/invoices/` | read OWNER+STAFF / create STAFF | List / create |
| GET | `/invoices/{id}/` | OWNER+STAFF | Invoice detail |
| GET | `/invoices/{id}/payments/` | OWNER+STAFF | Payment history |
| POST | `/invoices/{id}/payments/` | STAFF | Record customer payment |

## Order Convenience Endpoint

If compatible with the existing order architecture:

`POST /orders/{id}/invoice/`

It must prevent duplicate invoices for the same order.

## Filters
Invoices:
- customer
- order
- status
- date_from
- date_to
- page

Payments:
- invoice
- payment_method
- date_from
- date_to
- page

Use the established pagination convention.

## Error Contract
Continue using:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Invoice responses should expose customer/order, items, subtotal, total, paid, balance, status and payment count.
