# Saamu Tailors — Phase 5 API Contract

All endpoints use `/api/v1/`.

## Tailors
| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/tailors/` | OWNER + STAFF | List/search/filter |
| GET | `/tailors/{id}/` | OWNER + STAFF | Detail |
| POST | `/tailors/` | STAFF | Create |
| PATCH | `/tailors/{id}/` | STAFF | Edit |
| POST | `/tailors/{id}/archive/` | STAFF | Archive |
| POST | `/tailors/{id}/restore/` | STAFF | Restore |

Support active/archived/all filtering and pagination.

## Piece Rates
| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/piece-rates/` | OWNER + STAFF | List |
| POST | `/piece-rates/` | STAFF | Create |
| PATCH | `/piece-rates/{id}/` | STAFF | Update/deactivate |

Do not delete rates if that could compromise historical interpretation.

## Work Assignments
| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/work-assignments/` | OWNER + STAFF | Workload list |
| GET | `/work-assignments/{id}/` | OWNER + STAFF | Detail |
| POST | `/work-assignments/` | STAFF | Assign work |
| PATCH | `/work-assignments/{id}/` | STAFF | Safe operational update |
| POST | `/work-assignments/{id}/status/` | STAFF | Status transition |

Recommended filters: tailor, order, garment_type, status, date_from, date_to.

## Earnings
| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/tailors/{id}/earnings/` | OWNER + STAFF | Tailor earnings |
| GET | `/tailor-earnings/summary/` | OWNER + STAFF | Filtered summary |

Expose completed quantity, earnings, date range, and garment/work-type breakdown.

## Error Contract
Continue the existing format:
```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "..."
  }
}
```
