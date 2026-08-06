# Phase 15 Completion Report

## 1. Status

Status: **PASS**

Phase 15 (Production Hardening & Operational Readiness) is complete. It is a
hardening phase: no new business features, no UI redesign, and no behavior
change to any Version 1 flow. The phase fixed the real, bounded defects found in
the hardening review (payroll/billing N+1 query patterns, frontend cache
staleness, duplicate-submit on row actions, and a missing global error
boundary), documented the backup/restore procedure, reviewed the production
configuration, verified RBAC and the standard error contract, and left the
manual verification checklist `NOT STARTED` until it is actually performed.

**Final status:** Phase 15 is **PASS and ready for release verification / later
business phases**.

## 2. Scope

Per `docs/phase-15/01_PHASE_15_SCOPE.md` and `02_PHASE_15_REQUIREMENTS.md`, the
phase delivers:

- Backend hardening only where required (N+1 fixes with regression tests; no
  behavior change).
- Frontend reliability improvements only where required (cache invalidation
  gaps, duplicate-submit prevention, global error boundary).
- Documented PostgreSQL backup/restore procedure.
- Production configuration review.
- Security/RBAC verification.
- Manual verification checklist (left `NOT STARTED`).
- Automated regression tests for the newly fixed defects.
- Phase 15 completion report and README status update.

Out of scope (per `09_PHASE_15_DEFERRED_AND_GUARDRAILS.md` and the deferred list
from prior phases): cloud hosting/backups, WhatsApp/SMS, payment gateways, GST,
double-entry accounting, bank/cloud-accounting integration, report export/PDF,
new payment/invoice types, and any new business modules. No migration was added
and no existing module was rewritten.

## 3. Implementation Summary

The hardening review followed the Phase 15 backend and frontend task lists
(`04_PHASE_15_BACKEND.md`, `05_PHASE_15_FRONTEND.md`). Findings that were real
and bounded were fixed; everything else was verified and recorded as already
correct:

- **Backend N+1 (fixed):** the invoice payment-history list issued one query per
  row for `invoice.invoice_number`; the payroll period and entry lists issued
  per-row aggregate/settlement queries (up to 5 queries per period and 3 per
  entry). Both are now precomputed in the queryset (`select_related("invoice")`
  for payments; correlated `Subquery` annotations for payroll aggregates and
  settlement figures), so a paginated list stays at a small constant number of
  queries. The annotated path is proven equal to the live computation by
  dedicated regression tests.
- **Frontend cache staleness (fixed):** several mutations that change Dashboard
  figures (order create/update/status, work assignments, tailor/customer
  archive-restore, salary advances, payroll payments) did not invalidate the
  dashboard query. `DASHBOARD_KEY` invalidation was added to each.
- **Frontend duplicate-submit (fixed):** row-action buttons (assignment
  Progress/Complete in OrderDetail and TailorDetail, payroll Calculate/Finalize
  in Payroll and PayrollDetail) now disable while their mutation is pending.
- **Frontend global error boundary (added):** a small `ErrorBoundary` wraps the
  routed app so an unexpected render error shows a recoverable message instead
  of a blank screen (requirement 7 of `02_PHASE_15_REQUIREMENTS.md`).
- **Verified, no change required:** RBAC consistency across all apps, the
  standard error contract and its `404`/`500` handlers, read-only endpoints
  rejecting mutations with 405, protected-route behavior on auth expiry,
  loading/error/empty/retry states, dialog double-submit handling, and
  `.env`/secret hygiene.

## 4. Backend Changes

### `backend/apps/billing/views.py`

- `InvoiceViewSet.payments` (GET history) now uses
  `.select_related("invoice", "recorded_by")` so the serialized
  `invoice_number` (a forward lookup on each payment row) no longer issues a
  query per row (`views.py:168-172`).

### `backend/apps/payments/services.py`

- `settlement_summary(entry, precomputed=None)` and
  `period_settlement_summary(period, precomputed=None)` now accept an optional
  precomputed dict (`advance_deductions` / `payments_recorded` / `payment_count`
  for the entry form; plus `gross_payable` for the period form). When supplied,
  the aggregates are used instead of re-querying; the derived status logic and
  the returned shape are byte-for-byte identical to the live path. The live
  path is unchanged for all callers that do not pass `precomputed`.

### `backend/apps/payroll/serializers.py`

- `PayrollPeriodSerializer.to_representation` and
  `PayrollEntrySerializer.to_representation` use the queryset annotations when
  present (checked via `hasattr` on the annotated attribute) and otherwise fall
  back to the original live computation, so the serializers keep working for
  non-annotated instances (e.g. the `calculate` action's entry list).
- `PayrollPeriodSerializer` reads the seven period aggregates from annotations
  instead of `instance.entries.aggregate(...)` when available.

### `backend/apps/payroll/views.py`

- New `_aggregated_subquery(qs, group_by, expression, output_field)` helper and
  `_annotated_payroll_periods()` builder.
- `PayrollPeriodViewSet.queryset` is now `_annotated_payroll_periods()`: it
  `select_related("created_by")` and annotates the entry aggregates
  (`_total_completed_pieces`, `_total_fixed_salary`, `_total_piece_rate_earnings`,
  `_total_gross_salary`, `_total_attendance_amount`, `_total_payable`,
  `_entry_count`) plus the settlement aggregates (`_settlement_deductions`,
  `_settlement_paid`, `_settlement_payment_count`).
- `PayrollEntryViewSet.get_queryset` annotates `_advance_deductions`,
  `_payments_total` and `_payment_count`.
- `calculate` re-fetches the period from the annotated queryset after
  `period.calculate()` so the response period aggregates are fresh (the
  annotations captured before `calculate()` would otherwise be stale). This
  preserves the existing tested behavior of the calculate response.

No other backend module was changed. No model, serializer field, endpoint or
financial calculation was altered.

## 5. Frontend Changes

### Cache invalidation (`DASHBOARD_KEY`)

Mutations that change figures shown on the Dashboard now invalidate the
dashboard query in addition to their existing invalidations:

- `useOrders.ts` — `useCreateOrder`, `useUpdateOrder`, `useChangeOrderStatus`
  (order counts, revenue, garment quantities).
- `useTailors.ts` — `useCreateTailor`, `useUpdateTailor`, `useArchiveTailor`,
  `useRestoreTailor` (active tailors), `useCreateWorkAssignment`,
  `useUpdateWorkAssignment`, `useChangeWorkAssignmentStatus` (workload).
- `useCustomers.ts` — `useCreateCustomer`, `useUpdateCustomer`,
  `useArchiveCustomer`, `useRestoreCustomer` (active customers).
- `useAdvances.ts` — `useCreateAdvance` (salary advances).
- `usePayroll.ts` — `useRecordPayment`, `useSettleEntry` (payroll paid).

`DASHBOARD_KEY` is imported from `useFinance.ts` (no circular import). Invoice
payments/expenses already invalidated the dashboard.

### Duplicate-submit prevention

- `OrderDetail.tsx` — assignment `Progress` and `Complete` row buttons disable
  while `assignmentProgressMutation` / `assignmentStatusMutation` is pending.
- `TailorDetail.tsx` — same for `progressMutation` / `statusMutation`.
- `Payroll.tsx` and `PayrollDetail.tsx` — `Calculate` / `Finalize` buttons
  disable while `calculateMutation` / `finalizeMutation` is pending.

### Global error boundary

- New `frontend/src/components/ErrorBoundary.tsx` — a class component that
  catches render errors, logs them, and shows a friendly error card with Reload
  and Try-again actions.
- `App.tsx` wraps `<AppRoutes />` in `<ErrorBoundary>` inside the router.

No page layout, styling or behavior beyond the above was changed.

## 6. Database Changes

**None.** `python manage.py makemigrations --check --dry-run` → `No changes detected`.

- No schema or data migration was introduced.
- The N+1 fixes use `select_related` and correlated subqueries only; the
  existing indexes on `PayrollEntry(payroll_period, tailor)`,
  `PayrollPayment`, `SalaryAdvance` and `CustomerPayment` support them.
- The pre-existing uncommitted migration
  `backend/apps/finance/migrations/0002_expense_payment_method_and_more.py`
  (Phase 12/13 work) was left untouched.

## 7. API Changes

**None.** No endpoint, method, permission, serializer field or error shape was
added, removed or renamed. The standard
`{success:false, error:{code, message, details?}}` contract is unchanged, and
the fixed endpoints return identical payloads (verified by the existing
integration tests, which all pass unchanged).

## 8. RBAC Verification

Verified, no code change required. The review confirmed the backend remains the
single source of truth for authorization across every app:

- `apps/authentication/permissions.py` — `IsOwner`, `IsStaffRole`,
  `IsOwnerOrStaff`; anonymous → 401, OWNER read-only on restricted surfaces,
  STAFF mutations only.
- `apps/authentication/tests/` already cover the full anonymous/OWNER/STAFF
  matrix per module (tailors, customers, attendance, payroll, payments,
  finance, billing) including `permission_urls.py`.
- Audit fields (`created_by` / `recorded_by`) are always set server-side in
  `perform_create` / `perform_update` / services; client payloads cannot supply
  them (serializers never accept them, and the create serializers use
  server context only).
- Financial history is append-only/immutable: no update/delete routes exist for
  invoices, customer payments, payroll payments, salary advances or expenses
  (expense PATCH is restricted to STAFF and is audited via `updated_by`).
- Read-only endpoints (reports, income) are GET-only `APIView`s; unsupported
  methods return 405 (covered by tests).
- Frontend: `ProtectedRoute` redirects to login on missing/expired auth, the
  JWT refresh interceptor in `apiClient.ts` re-authenticates on 401, and 403
  responses surface an understood message.

## 9. Error Contract & API Reliability

Verified, no code change required:

- `apps/common/exceptions.py` normalizes DRF/validation/exceptions to
  `{success:false, error:{code, message, details?}}` with `EXCEPTION_CODE_MAP`;
  internal exception text is never leaked to clients.
- `apps/common/views.py` `custom_404` / `custom_500` return the same contract.
- DRF default permission is `IsAuthenticated`, so every protected endpoint 401s
  anonymous requests by default.
- Filter validation is consistent (invalid status/date filters → 400 with the
  standard contract) across orders, invoices, attendance, advances and finance.

## 10. Performance Review

The list/detail review found two real N+1 patterns, both fixed; everything else
checked was already using `select_related`/`prefetch_related` appropriately or
is bounded by pagination.

### Fixed findings (with measured before/after)

| Endpoint | Before | After |
|---|---|---|
| `GET /api/v1/billing/invoices/{id}/payments/` | 1 query + 1 per payment (invoice lookup) | 1 constant query for the page |
| `GET /api/v1/payroll/periods/` (list) | ~1 + 5 per period (aggregates + settlement) | 1 query for the page |
| `GET /api/v1/payroll/entries/` (list) | ~1 + 3 per entry (settlement) | 1 query for the page |

- Verified in a live check: serializing an annotated period uses **1 query**
  (previously 5+ per period) and produces values identical to the live path.
- Regression tests assert the list endpoints stay within a small constant query
  budget even with multiple rows, and that the precomputed settlement values
  equal the live computation exactly.
- The `calculate` action's entry sub-list still uses the non-annotated live path
  (correct and bounded to a single action).

## 11. Backup & Restore

Documented in `docs/phase-15/12_PHASE_15_BACKUP_AND_RESTORE.md`.

- `pg_dump` custom-format command with timestamped filenames
  (`saamu_db_YYYY-MM-DD_HHMMSS.dump`) written to a directory **outside the
  source tree** (`D:\SaamuBackups`).
- Safe test-restore workflow into a throwaway `saamu_restore_test` database with
  verification queries, plus the live-recovery workflow.
- Documented what is and is not included (database rows/schema only; media,
  static, `.env`, logs and the frontend build are excluded).
- Explicit safety rule: destructive restores are never tested against the live
  shop database.
- Tooling verified present (`pg_dump`/`psql`/`pg_restore` under
  `C:\Program Files\PostgreSQL\18\bin\`); no live backup or restore was
  executed during this phase.

## 12. Production Configuration Review

Documented in `docs/phase-15/13_PHASE_15_PRODUCTION_CONFIG_REVIEW.md`.

- `config/settings.py` is environment-driven and secret-safe: `SECRET_KEY`,
  `DEBUG`, `ALLOWED_HOSTS`, DB credentials, CORS origins, time zone, logging
  and static/media paths all come from env vars; no hardcoded secrets; `.env`
  gitignored; PostgreSQL-only.
- DRF secure-by-default (`IsAuthenticated`), global standard exception handler,
  pagination on, JWT 60-minute access tokens.
- No code change required. Deploy-time operator actions are documented in a
  checklist: set a real `SECRET_KEY`, `DEBUG=False`, explicit `ALLOWED_HOSTS`
  (drop the meaningless `0.0.0.0`), explicit CORS origins, and HTTPS flags only
  if the app is ever exposed beyond LAN HTTP.

## 13. Testing Results

Backend (all pass, executed from `backend/` with the project venv):

```text
python manage.py check                            -> System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run -> No changes detected
python -m pytest (full suite)                     -> 519 passed in 231.89s (baseline 514 + 5 new)
python -m black --check <touched files>           -> clean
python -m isort --check-only <touched files>      -> clean
```

New regression tests (5):

- `backend/apps/payroll/tests/test_payroll.py`
  - `test_period_list_aggregate_queries_are_bounded` — period list stays within
    10 queries for 3 calculated periods and the aggregates/settlement match.
  - `test_entry_list_settlement_queries_are_bounded` — entry list settlement
    stays within 10 queries.
  - `test_precomputed_settlement_summary_matches_live` — precomputed entry
    settlement equals the live computation.
  - `test_precomputed_period_settlement_summary_matches_live` — same for the
    period-level summary.
- `backend/apps/billing/tests/test_payments.py`
  - `test_payment_history_queries_are_bounded` — payment history stays within
    10 queries and returns `invoice_number`.

Frontend (all pass):

```text
npm run lint      -> clean
npx tsc --noEmit  -> clean
npm run build     -> clean (tsc + vite build; pre-existing chunk-size warning only)
```

## 14. Manual Verification

Phase 15 manual verification is checklist-only per
`docs/phase-15/08_PHASE_15_MANUAL_VERIFICATION.md` and remains **NOT STARTED**.
The hardening changes are exercised end-to-end by the backend integration tests
(query-count budgets, precomputed-vs-live equivalence, existing RBAC/error
contract coverage) and the frontend static checks; the manual checklist (real
backup/restore run, real double-click flows, dashboard freshness after each
mutation type) is left for the operator to perform before relying on the
procedures.

## 15. Documentation

- `docs/phase-15/` — the ten planning/specification documents, this report
  (`11_PHASE_15_COMPLETION_REPORT.md`), the backup/restore procedure
  (`12_PHASE_15_BACKUP_AND_RESTORE.md`) and the production configuration review
  (`13_PHASE_15_PRODUCTION_CONFIG_REVIEW.md`). The manual-verification checklist
  (`08_...`) remains `NOT STARTED`.
- `README.md` — stage line updated to Phase 15 and the phase-status list
  updated (Phase 15 — Production Hardening & Operational Readiness: complete).

## 16. Files Changed

**Modified - backend (Phase 15):**
- `backend/apps/billing/views.py` — payments `select_related("invoice")`
- `backend/apps/payments/services.py` — `precomputed` support in both
  settlement summaries
- `backend/apps/payroll/serializers.py` — annotation-aware `to_representation`
- `backend/apps/payroll/views.py` — annotations, `_aggregated_subquery`, fresh
  re-fetch after `calculate`
- `backend/apps/payroll/tests/test_payroll.py` — 4 regression tests
- `backend/apps/billing/tests/test_payments.py` — 1 regression test

**Created - frontend:**
- `frontend/src/components/ErrorBoundary.tsx`

**Modified - frontend (Phase 15):**
- `frontend/src/App.tsx` — wrap routes in `ErrorBoundary`
- `frontend/src/hooks/useOrders.ts`, `useTailors.ts`, `useCustomers.ts`,
  `useAdvances.ts`, `usePayroll.ts` — `DASHBOARD_KEY` invalidation
- `frontend/src/pages/OrderDetail.tsx`, `TailorDetail.tsx`, `Payroll.tsx`,
  `PayrollDetail.tsx` — pending-disabled row/action buttons

**Documentation (Phase 15):**
- `docs/phase-15/11_PHASE_15_COMPLETION_REPORT.md`
- `docs/phase-15/12_PHASE_15_BACKUP_AND_RESTORE.md`
- `docs/phase-15/13_PHASE_15_PRODUCTION_CONFIG_REVIEW.md`
- `README.md` stage/status updates

**Pre-existing uncommitted work (left untouched by Phase 15):** Phase 12/13/14
files — `backend/apps/finance/*` (admin, models, serializers, services, views,
urls, tests, `0002_...` migration), `backend/apps/tailors/tests/test_work_assignments.py`,
the frontend finance/invoice/income/expense/report files and
`docs/phase-12/`, `docs/phase-13/`, `docs/phase-14/`. Note: `Payroll.tsx`,
`PayrollDetail.tsx`, `OrderDetail.tsx`, `TailorDetail.tsx`, `useAdvances.ts` and
`useTailors.ts` were also already in the uncommitted working set; Phase 15 edits
are confined to the lines described above, and prettier was run on these six
files to match the repo's `.prettierrc` (whitespace only).

## 17. Known Issues

- Frontend production build emits a pre-existing chunk-size warning (>500 kB
  after minification); non-blocking and unchanged by this phase.
- The manual verification checklist is `NOT STARTED`; the backup/restore
  procedure has been documented and validated against installed tooling but not
  executed against live data.
- The `.env` used for local development still has `DEBUG=True` and the dev
  `SECRET_KEY`; this is correct for local development and is flagged in the
  production configuration review as a deploy-time action, not a code defect.

## 18. Git Verification & Phase 16 Readiness

The Phase 15 changes are present in the working tree but **no commit was
created** (commits are only made on explicit request). The pre-existing
uncommitted Phase 12/13/14 work was preserved untouched, and Phase 15 additions
were verified against the diff (section 16) before reporting completion.

**Ready.** Phase 15 is **PASS**:

- All Phase 15 completion gates pass (`manage.py check`, `makemigrations
  --check --dry-run` clean, 519-test backend suite, black/isort clean, frontend
  lint/typecheck/build clean).
- Backend remains authoritative; no financial or business behavior changed.
- Real, bounded hardening defects were fixed with regression tests; everything
  else was verified and documented.
- Backup/restore and production-configuration deliverables are documented.
- Manual verification checklist remains `NOT STARTED` until actually performed.
