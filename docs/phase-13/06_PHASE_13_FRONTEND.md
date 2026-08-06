# Phase 13 — Frontend Specification

Use the existing React + TypeScript finance architecture, React Query, service patterns, ERP design and existing dashboard components.

## Income View
Provide:
- total income
- meaningful income/payment count
- payment-method breakdown
- payment-type breakdown where useful
- date/date-range filtering
- payment-method filtering
- filtered income results

## Financial Source
All authoritative totals come from backend responses. Do not calculate authoritative totals from visible table rows.

## Refund Display
Clearly distinguish customer payments and refunds where payment history is shown. Net income must reflect refunds.

## Permissions
OWNER and STAFF can read income. No payment mutation controls belong on the Income page. Payment mutations remain under Invoice/Billing.

## Cache
When a payment/refund changes underlying data, invalidate/refetch relevant income and dashboard queries.
