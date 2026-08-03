# Phase 9 — Frontend Specification

Follow the established architecture:

`types → service → hooks → dialogs/components → pages → routes`

## Invoices Page
Route: `/invoices`

Features:
- Filter by invoice number/customer/order.
- Status filter.
- Date range.
- Pagination.
- Total / paid / balance columns.
- STAFF-only Create Invoice.
- OWNER read-only.

## Invoice Detail
Route: `/invoices/:id`

Display:
- Invoice number/date.
- Customer details.
- Order number.
- Garment/item table.
- Subtotal.
- Total.
- Paid.
- Balance due.
- Status.
- Payment history.
- STAFF-only Record Payment.

## Record Payment Dialog
Fields:
- amount
- payment date
- payment method
- reference
- notes

Show total, paid, current balance and maximum payable.

Client validation should mirror backend rules; backend remains authoritative.

## Order Integration
Provide a non-invasive way from an order to:
- Create invoice if none exists.
- View invoice if one exists.

Do not redesign the existing order workflow.

## Navigation
Add an Invoices sidebar item and route.
