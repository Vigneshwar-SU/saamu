# Saamu Tailors — Phase 5 Frontend Requirements

## Tailors Page
Replace the placeholder with:
- Search
- Active/Archived/All filter
- Pagination
- Name/mobile
- Active status
- Workload summary
- Earnings summary
- STAFF: Add/Edit/Archive/Restore
- OWNER: view-only

## Tailor Detail
Show profile, status, current workload, assigned work, completed work, earnings, date-range filter, and garment/work-type breakdown.

## Work Assignment
STAFF can:
1. Select active tailor.
2. Select eligible order item.
3. See order/customer/garment context.
4. See remaining quantity.
5. Select applicable piece rate.
6. Enter assigned quantity.
7. Submit.

Client validation is UX only; backend remains authoritative.

## Work Status
Display valid actions only:
`ASSIGNED → IN_PROGRESS → COMPLETED`

Completion must validate quantity and show calculated earnings where practical.

## Earnings
Provide date range, completed pieces, total earned, garment breakdown, and assignment detail.

Reuse existing MUI, layout, sidebar, API client, TanStack Query, loading/error/empty states, and role-aware UI. Do not introduce another UI framework.
