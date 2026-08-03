# Phase 7 — API Specification

All endpoints use `/api/v1/` and the existing standardized error shape.

## Advances
| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/advances/` | OWNER+STAFF | List/filter advances |
| POST | `/advances/` | STAFF | Create advance |
| GET | `/advances/{id}/` | OWNER+STAFF | View advance |

Filters: tailor, status, date_from, date_to, page.

## Payroll Settlement
| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/payroll/entries/{id}/settlement/` | OWNER+STAFF | Settlement summary |
| GET | `/payroll/entries/{id}/payments/` | OWNER+STAFF | Payment history |
| POST | `/payroll/entries/{id}/payments/` | STAFF | Record payment |
| POST | `/payroll/entries/{id}/settle/` | STAFF | Optional explicit full-settlement action |

## Validation
- Target payroll must belong to a FINALIZED period.
- Payment amount > 0.
- Payment cannot exceed server-calculated outstanding.
- Tailor relationship must match.
- Invalid method → 400 standardized error.
- Invalid target → 404.
- OWNER mutation → 403.
- Anonymous → 401.

Settlement responses should expose gross payable, advance deductions, payments, outstanding payable, and status.
