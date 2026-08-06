# Phase 17 — Architecture

## Architectural decision
Use the existing Reports aggregation as the single source of truth and add a thin export layer above it.

```text
Reports UI
  → export request
  → Reports export endpoint
  → build_reports_summary(date_from, date_to)
  → CSV/PDF renderer
  → downloadable response
```

No report database model is required.

## Backend boundaries
Recommended structure:
- `apps/finance/services.py` remains authoritative for aggregation.
- A focused export service/module transforms the summary into CSV/PDF.
- `apps/finance/views.py` adds GET-only export views.
- Finance URLs expose the export routes.

The exact module location must be chosen after repository inspection.

## Suggested endpoints
```text
GET /api/v1/reports/export/csv/
GET /api/v1/reports/export/pdf/
```

Optional:
```text
?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
```

These are proposed names and must be reconciled with existing routing conventions during implementation.

## Data consistency
The export layer must call the same report service used by `ReportsSummaryView`. It must not independently calculate income, refunds, expenses, net position, or other authoritative figures.

## Security
Export endpoints are ordinary authenticated read endpoints. They must never expose Phase 16 management-command functionality or accept arbitrary paths/commands.

## Frontend
Use the existing API client/service conventions and a small download helper if one already exists. Do not calculate report values in React.
