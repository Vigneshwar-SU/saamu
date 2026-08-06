# Phase 17 — API Contract

## CSV
```http
GET /api/v1/reports/export/csv/
```

Optional query parameters:
```text
date_from=YYYY-MM-DD
date_to=YYYY-MM-DD
```

Successful response:
```text
HTTP 200
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="saamu-tailors-report-....csv"
```

## PDF
```http
GET /api/v1/reports/export/pdf/
```

Successful response:
```text
HTTP 200
Content-Type: application/pdf
Content-Disposition: attachment; filename="saamu-tailors-report-....pdf"
```

## Authorization
| User | Result |
|---|---|
| Anonymous | 401 |
| OWNER | 200 |
| STAFF | 200 |

## Validation
Invalid/reversed dates must use the existing Reports `_parse_range` and standard error contract.

## Mutation methods
POST/PUT/PATCH/DELETE are unsupported and should return 405.

## Data contract
For the same date range, exported values must correspond to `GET /api/v1/reports/summary/`. The export does not introduce a second source of business truth.

## Compatibility
The Phase 14 summary endpoint remains unchanged.
