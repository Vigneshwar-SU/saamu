# Phase 14 — API Specification

All APIs follow `/api/v1/` and the existing standard error contract.

## Reports Summary
Provide a read-only reporting summary endpoint under the existing API structure.

Expose the business insights required by Phase 14, such as:
- order counts and status distribution
- customer/order activity
- tailor workload indicators
- income
- expenses
- net financial position where meaningful
- payment/refund-aware financial values

## Filters
Support applicable:
- `date_from`
- `date_to`

Additional filters only where justified by the scope and existing data.

Invalid filters use the project's standard validation error.

## Access
- OWNER: read.
- STAFF: read.
- Anonymous: 401.

No report endpoint may create, update, or delete business records.

All report totals are calculated from authoritative backend records.
