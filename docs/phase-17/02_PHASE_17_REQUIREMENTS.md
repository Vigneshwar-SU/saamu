# Phase 17 — Requirements

## Functional requirements

### R1 — Reports remains authoritative
All exported values must originate from the existing Phase 14 reporting aggregation. Do not duplicate financial/business arithmetic in export views or frontend code.

### R2 — CSV export
Provide a deterministic, spreadsheet-readable CSV containing:
- applied date range;
- order summary;
- order status distribution;
- garment quantities;
- customer activity;
- tailor workload;
- income summary;
- expense summary;
- net position;
- payroll paid;
- salary advances;
- payment-type breakdown;
- expense-category breakdown.

Clearly label logical sections and keep column ordering stable.

### R3 — PDF export
Provide a human-readable PDF containing:
- title;
- generated date/time;
- selected date range;
- financial summary;
- order summary;
- customer activity;
- tailor workload;
- payroll/settlement summary;
- income-by-payment-type;
- expenses-by-category.

The PDF is a report snapshot, not an invoice or accounting document.

### R4 — Date range
Exports use the same optional inclusive `date_from` and `date_to` semantics as Reports:
- both omitted → all time;
- `date_from` only → from that date onward;
- `date_to` only → through that date;
- both → inclusive range;
- invalid date → 400;
- reversed range → 400.

### R5 — Permissions
Only authenticated OWNER and STAFF users may export. Anonymous → 401. No new role.

### R6 — Read-only
Exports must not create, update, delete, settle, archive, or otherwise mutate business data. Unsupported mutation methods → 405.

### R7 — Frontend
Reports exposes:
- Export CSV.
- Export PDF.

Buttons use the currently applied date range, not uncommitted filter inputs.

### R8 — Export state
Prevent accidental duplicate export requests, show loading state, surface recoverable errors, and preserve current Reports state.

### R9 — File naming
Use deterministic safe names, e.g. `saamu-tailors-report-all-time.csv` or `saamu-tailors-report-2026-01-01-to-2026-01-31.pdf`. Never accept path separators or arbitrary filenames.

### R10 — No sensitive leakage
Exports must not contain passwords, JWTs, database credentials, environment variables, stack traces, or security secrets.

## Compatibility
- Existing Reports summary API remains unchanged.
- Existing business modules remain unchanged.
- Phase 16 backup/restore remains untouched.
- No schema migration should be necessary.

## Engineering
- Reuse existing services/types where practical.
- Keep export generation isolated from destructive tooling.
- Generate authoritative exports server-side.
- Add regression tests for calculations, filtering, RBAC, content disposition, and non-mutation.
