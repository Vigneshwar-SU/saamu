# Phase 8 — API Specification

All endpoints use `/api/v1/`.

## Income
- `GET /income/` — OWNER + STAFF
- `POST /income/` — STAFF
- `GET /income/{id}/` — OWNER + STAFF

Filters: `date_from`, `date_to`, `category`, `page`.

## Expenses
- `GET /expenses/` — OWNER + STAFF
- `POST /expenses/` — STAFF
- `GET /expenses/{id}/` — OWNER + STAFF

Filters: `date_from`, `date_to`, `category`, `page`.

## Dashboard
- `GET /dashboard/summary/` — OWNER + STAFF

Query:
- `date_from`
- `date_to`

Response should include financial summary, operational summary, order status counts, garment summary, workload summary, recent income and recent expenses.

Use the existing `{success:false,error:{code,message,details?}}` error contract and existing pagination conventions.
