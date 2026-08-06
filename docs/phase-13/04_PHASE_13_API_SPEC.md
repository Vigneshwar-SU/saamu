# Phase 13 — API Specification

Use the existing `/api/v1/` conventions and standard error contract.

## Income List
`GET /api/v1/income/`

Return income derived from actual customer-payment data.

Support applicable filters including:
- `date_from`
- `date_to`
- `payment_method`
- payment type where supported

## Income Summary
`GET /api/v1/income/summary/`

Return server-derived values such as:
- `total_income`
- meaningful income/payment count
- `by_payment_method`
- `by_payment_type` where appropriate
- filtered totals

## Dashboard
If dashboard income already exists, make it use the same authoritative aggregation service. Do not duplicate the calculation.

## Access
- OWNER: read.
- STAFF: read.
- Anonymous: 401.
- Client-supplied financial totals are never authoritative.
- Invalid filters follow the project's standard 400 error contract.

## Refunds
Refunds decrease net income.
