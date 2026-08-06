# Phase 12 — API Specification

All endpoints use `/api/v1/`.

## Expense List
`GET /api/v1/expenses/`
OWNER/STAFF allowed; anonymous 401.

## Create Expense
`POST /api/v1/expenses/`
STAFF allowed; OWNER 403; anonymous 401.

Example:
```json
{
  "category": "RENT",
  "amount": 5000,
  "expense_date": "2026-08-05",
  "description": "Monthly shop rent",
  "payment_method": "CASH"
}
```

`recorded_by` must never be client-supplied.

## Detail
`GET /api/v1/expenses/{id}/`
OWNER/STAFF may view.

## Filtering
Support useful category, payment method, date/date-range filters as required by the UI.

## Summary
If appropriate:
`GET /api/v1/expenses/summary/`

Possible response:
```json
{
  "total_expenses": 10000,
  "expense_count": 12,
  "by_category": [],
  "by_payment_method": []
}
```

All values must be derived server-side.

## Errors
Use the existing error contract:
```json
{"success": false, "error": {"code": "...", "message": "...", "details": {}}}
```

Follow existing `COERCE_DECIMAL_TO_STRING=False` behavior.
