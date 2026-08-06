# Phase 17 Completion Report

## 1. Status

**PASS** — implementation, automated tests, and documentation are complete.
Live manual verification of the export workflow (clicking Export CSV/PDF in a
running browser against the real shop database) was **NOT PERFORMED** during
this phase; the manual-verification checklist (`08_PHASE_17_MANUAL_VERIFICATION.md`)
remains **NOT STARTED** (see section 12).

## 2. Scope

Phase 17 (Reports Export) added CSV and PDF export to the existing Phase 14
Reports module:

- `GET /api/v1/reports/export/csv/` and `GET /api/v1/reports/export/pdf/` —
  read-only, OWNER/STAFF, honoring the same inclusive `date_from` / `date_to`
  range semantics as the reports page.
- A thin export layer backed **solely** by the authoritative Phase 14
  `build_reports_summary` aggregation — the same single source of truth used
  by `ReportsSummaryView` — so an exported file can never disagree with the
  reports page and no second source of truth is introduced.
- Deterministic, UTF-8 CSV (orders/status distribution/garment quantities,
  customers, tailor workload, financial summary, income by payment
  method/type, expenses by category/payment method) with exact two-decimal
  money rendering.
- A human-readable PDF snapshot (title, generated date/time, report period,
  financial summary, orders, customers, tailor workload, payroll &
  settlements, income by payment type, expenses by category).
- Frontend Export CSV / Export PDF buttons on the Reports page that download
  the file for the **applied** range only, with loading/disabled states,
  duplicate-submit protection, recoverable error display, and no navigation.
- Safe, range-derived file names via `Content-Disposition`.

Out of scope (deferred, not implemented): scheduled exports, WhatsApp/SMS/email,
cloud deployment, cloud backup automation, payment gateways, GST, double-entry
accounting, new payment/invoice types, browser-accessible backup/restore, UI
redesign, generic file management.

## 3. Implementation Summary

The phase added a read-only presentation layer over the existing reports
aggregation. The backend export service (`report_exports.py`) is a pure
function of the `build_reports_summary` result and returns bytes only; it reads
no records and can never mutate business data. The export views reuse the
existing `_parse_range` validation (inclusive boundaries; invalid/reversed
ranges → 400 with the standard error contract) and the existing `IsOwnerOrStaff`
permission (anonymous → 401). PDF rendering uses ReportLab with
`pageCompression=0` so test assertions can read text directly from the raw byte
stream without a PDF parser.

Delivered:

- `backend/apps/finance/report_exports.py` — `build_csv_report(summary)` /
  `build_pdf_report(summary)`.
- `ReportsExportView` (initkwarg-selected `csv`/`pdf`) registered at
  `reports/export/csv/` and `reports/export/pdf/`.
- 17 focused tests covering the Phase 17 test specification.
- Frontend export service functions (blob + server-provided filename), a
  download helper, a `useReportExport` mutation, and Export buttons on the
  Reports page.
- `backend/requirements.txt` gained `reportlab>=4.2,<5.0` (the only new
  runtime dependency of the phase).
- `README.md` stage/status update and this completion report.

## 4. Backend Changes

| File | Change |
|---|---|
| `apps/finance/report_exports.py` | New export service module: deterministic UTF-8 CSV builder and ReportLab PDF builder, both pure functions of a `build_reports_summary` result. Exact money rendering via `Decimal.quantize` (never float artifacts); ASCII-safe PDF text; `pageCompression=0` for direct content assertions. |
| `apps/finance/views.py` | Added `ReportsExportView` (GET-only, `IsOwnerOrStaff`) with `_range_slug` / `_export_filename` helpers; `Content-Disposition: attachment; filename="saamu-tailors-report-<range>.csv\|pdf"`. Module docstring extended. |
| `apps/finance/urls.py` | Registered `reports/export/csv/` and `reports/export/pdf/` via `ReportsExportView.as_view(export_format=...)`. |
| `apps/finance/tests/helpers.py` | Added `reports_export_csv_url()` / `reports_export_pdf_url()`. |
| `apps/finance/tests/test_report_exports.py` | New: 17 tests covering the Phase 17 test specification. |
| `requirements.txt` | Added `reportlab>=4.2,<5.0` (installed in `.venv`; verified importable as 4.5.1). |

## 5. Frontend Changes

| File | Change |
|---|---|
| `services/financeService.ts` | Added `exportReportsCsv` / `exportReportsPdf` returning `{ blob, filename }`; filename comes from the server's `Content-Disposition` header with a safe fallback. |
| `utils/download.ts` | New: `downloadBlob` (object URL + anchor download, no navigation) and `extractDownloadFilename`. |
| `hooks/useReports.ts` | Added `useReportExport` (React Query mutation) and `ReportExportFormat`. |
| `pages/Reports.tsx` | Added Export CSV / Export PDF buttons (icon + label) using the **applied** range; both disabled while an export is pending (duplicate-submit protection) with "Exporting…" label; recoverable inline error alert that keeps report data and allows retry. |

The frontend never computes authoritative totals — exports request the file
from the server for the applied range, and the report page data is unchanged by
an export.

## 6. Database Changes

None. No models, no migrations, no schema change.
`python manage.py makemigrations --check --dry-run` reports "No changes detected".

## 7. API Changes

Two new read-only endpoints (both behind `IsOwnerOrStaff`, GET-only):

- `GET /api/v1/reports/export/csv/?date_from=&date_to=` →
  `text/csv; charset=utf-8`, `Content-Disposition: attachment`.
- `GET /api/v1/reports/export/pdf/?date_from=&date_to=` →
  `application/pdf`, `Content-Disposition: attachment`.

Behavior mirrors `ReportsSummaryView` exactly: anonymous → 401; OWNER/STAFF →
200; invalid date → 400 `validation_error`; reversed range → 400;
POST/PUT/PATCH/DELETE → 405. Query parameters are optional and inclusive
(`date_from`/`date_to` inclusive boundaries). No existing endpoint or response
contract was changed.

## 8. RBAC & Security

- No new roles or permissions; the existing `IsOwnerOrStaff` model is reused.
- Anonymous requests → 401; both OWNER and STAFF can export.
- Exports are strictly read-only: only `GET` is defined, so a report export can
  never mutate business records (verified by test).
- No user-supplied filesystem path is accepted anywhere in the export flow.
- No secrets are exported: reports carry aggregate counts and totals only; a
  test seeds customer notes/phone data and asserts it never appears in the CSV
  or PDF bytes.
- File names are derived solely from the applied date range and a fixed prefix
  (e.g. `saamu-tailors-report-2026-08-01_to_2026-08-31.csv`), so they are always
  safe in `Content-Disposition`.
- Money values are exact two-decimal strings produced from `Decimal` — exported
  totals are reproducible and never floating-point artifacts.

## 9. Export Correctness

- CSV and PDF are both built from a single call to the authoritative
  `build_reports_summary(date_from, date_to)` — the identical aggregation the
  reports page renders — so exported values always agree with the page.
- Date semantics are identical to the reports page: `date_from`/`date_to`
  inclusive, applied consistently across every date-based metric; no range
  means all-time.
- CSV is deterministic: fixed section order, stable headers, exact two-decimal
  money, `\r\n` line endings, UTF-8.
- PDF is a printable snapshot with generated date/time and the selected range;
  all strings are ASCII-safe and `pageCompression=0` keeps content directly
  testable.

## 10. Testing Results

### Phase 17 focused tests (17 new in `apps/finance/tests/test_report_exports.py`)

Per the Phase 17 test specification:

- RBAC matrix: anonymous → 401 for both formats; OWNER and STAFF → 200 for
  both formats; mutation methods (POST/PUT/PATCH/DELETE) → 405.
- Range semantics: no-filter/all-time, `date_from` only, `date_to` only,
  combined range, inclusive boundaries, invalid date → 400
  `validation_error`, reversed range → 400.
- CSV structure: stable headers and section titles; exact money/count values
  (income, refunds, expenses, net position, order revenue, garment quantities,
  status distribution, payroll, advances); exported values match the
  authoritative `build_reports_summary` for every financial metric.
- PDF validity: `%PDF-1.` header, `%%EOF` trailer, non-trivial length; expected
  sections and exact amounts present; range filtering reflected in PDF amounts.
- Safe file names: `all-time`, `from_<date>`, `to_<date>`, `<from>_to_<to>`
  variants for both formats.
- No secrets / contact data leakage (notes, mobile number, customer name never
  in CSV or PDF).
- Read-only: customer/order/expense/payment counts unchanged after both exports.

### Backend gates

| Gate | Result |
|---|---|
| `python manage.py check` | PASS (0 issues) |
| `python manage.py makemigrations --check --dry-run` | PASS ("No changes detected") |
| Focused pytest (`apps/finance/tests/test_report_exports.py`) | PASS (17/17) |
| Full pytest suite | PASS (604/604) |
| `black --check apps/finance` | PASS |
| `isort --check-only apps/finance` | PASS |

### Frontend gates

| Gate | Result |
|---|---|
| `npm run lint` | PASS |
| `tsc` (via `npm run build`) | PASS |
| `npm run build` | PASS (pre-existing chunk-size warning only) |

## 11. Manual Verification

Status: **NOT STARTED** (per `08_PHASE_17_MANUAL_VERIFICATION.md`).

No live export was executed from a running browser against the real shop
database during this phase. Automated tests exercise the endpoints, RBAC, range
semantics, CSV/PDF content and file names, and the frontend builds cleanly, but
the human checklist — applying a date range, clicking Export CSV/PDF, verifying
the downloaded files open and match the on-screen report, checking the error
path, and confirming no navigation occurs — remains for a live session and does
not count as done.

## 12. Documentation

| Document | Status |
|---|---|
| `docs/phase-17/01..10` planning documents | Present (scope, requirements, architecture, backend, frontend, API, testing, manual verification, deferred/guardrails, deliverables). |
| `11_PHASE_17_COMPLETION_REPORT.md` | This report. |
| `08_PHASE_17_MANUAL_VERIFICATION.md` | Left **NOT STARTED** (unchanged). |
| `README.md` | Updated: current stage, Reports section export bullet, phase list. |
| `backend/requirements.txt` | Updated with `reportlab>=4.2,<5.0`. |

## 13. Files Changed

Backend (Phase 17 scope):

- `backend/apps/finance/report_exports.py` (new)
- `backend/apps/finance/views.py`
- `backend/apps/finance/urls.py`
- `backend/apps/finance/tests/test_report_exports.py` (new)
- `backend/apps/finance/tests/helpers.py`
- `backend/requirements.txt`

Frontend (Phase 17 scope):

- `frontend/src/services/financeService.ts`
- `frontend/src/utils/download.ts` (new)
- `frontend/src/hooks/useReports.ts`
- `frontend/src/pages/Reports.tsx`

Documentation:

- `docs/phase-17/11_PHASE_17_COMPLETION_REPORT.md`
- `README.md`

No migration files and no pre-existing Phase 12–16 uncommitted files were
modified by this phase.

## 14. Known Issues

- PDF text is rendered as ASCII with non-ASCII characters replaced; garment
  names, status labels and customer-facing strings are ASCII today, so no data
  loss is expected, but exotic Unicode in future labels would render with `?`.
- The frontend export buttons share a single `isPending` state, so while one
  export is running the other button is also disabled; this is intentional
  duplicate-submit protection, not an error.
- CSV has no UTF-8 BOM; plain UTF-8 is used per the Phase 17 documents (modern
  spreadsheet apps handle it fine; Excel older versions may need an import step).

## 15. Deferred Items

Per `09_PHASE_17_DEFERRED_AND_GUARDRAILS.md` (unchanged): WhatsApp/SMS/email
delivery, automated reminders, scheduled exports, cloud deployment, cloud
backup storage/automation, payment gateways, GST automation, double-entry
accounting, bank/cloud accounting integration, new payment/invoice types,
browser-accessible backup/restore, UI redesign, generic file management.

## 16. Git Verification

- No git commit was created (per Phase 17 deliverables: "Do not create a commit
  unless explicitly requested").
- No `git reset`, stash, checkout, clean, or discard was performed.
- `git status` / `git diff --stat` were reviewed at the end of the phase: only
  the Phase 17 file set above was added/modified.
- The untracked `docs/phase-17/` planning documents and the new
  `report_exports.py`, `test_report_exports.py` and `utils/download.ts` are part
  of this phase's deliverables and remain uncommitted with the rest of the work.

## 17. Phase 18 Readiness

Ready. Phase 17 leaves the reports module with deterministic, tested CSV/PDF
export on top of the single authoritative aggregation, all regression gates
green (604 backend tests, frontend lint/tsc/build), no schema changes, and no
new security surface beyond two read-only OWNER/STAFF endpoints. Phase 18 can
proceed with the next business module (scheduled exports/reminders, WhatsApp, or
cloud migration) on a stable base. The only outstanding item is the live
manual-verification checklist, which must be performed before the export
workflow is treated as proven against real shop data.
