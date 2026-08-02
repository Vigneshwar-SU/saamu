# Saamu Tailors — Phase 4 Frontend Specification

Use the existing React + TypeScript + MUI + TanStack Query architecture. Do not redesign the application shell.

## Orders page
Replace the Orders placeholder with:
- search
- status filter
- useful date filters
- pagination
- order table/list
- loading, empty, error/retry states
- order number, customer, garment summary, status, delivery date, amount and created date
- click row to open detail

## Create order — STAFF only
Sections:
1. Customer search/selection
2. Dates
3. Garment items
4. Measurement selection
5. Pricing
6. Notes
7. Save

Support SHIRT and PANT and multiple items. If required measurements do not exist, explain clearly and direct staff to the customer's measurement page.

## Detail
Show order number, customer, status/timeline, garments, quantities, measurement version/snapshot, pricing, notes, dates and collection information.

STAFF gets mutation controls. OWNER gets view-only UI.

## UI
Preserve:
- #1E3A8A primary
- #2563EB secondary
- #10B981 accent
- #F8FAFC background
- #FFFFFF surface
- 12px radius
- clean borders and subtle shadows
- no glassmorphism

Avoid page-level nested `100vh`/`overflow:auto` containers that break scrolling.
