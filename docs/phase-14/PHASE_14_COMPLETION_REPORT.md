# Phase 14 Completion Report

## 1. Status

Status: **PASS**

Phase 14 (Reports & Business Insights) is complete. It adds a read-only reporting layer over the authoritative Saamu modules: orders, customers, tailor workload, income, expenses and net position are all aggregated server-side on demand, never stored, and never re-entered. The reports reuse the Phase 13 income aggregation (`build_income_summary`) and Phase 12 expense aggregation (`build_expense_summary`) verbatim, so the Reports page can never disagree with the Income, Expenses or Dashboard pages.

**Final status:** Phase 14 is **PASS and ready for Phase 15**.

## 2. Scope

Per `docs/phase-14/01_PHASE_14_SCOPE.md`, the phase delivers:

- A read-only reports overview: order counts and status distribution, order revenue, garment quantities, customer activity (active, new, with orders), tailor workload, income (payment-derived, refund-aware), expenses, net position, payroll paid and salary advances.
- An overview page (the frontend Reports page) showing summary sections/cards and breakdowns.
- Date filtering (`date_from` / `date_to`, inclusive) applied consistently across every date-based metric; reversed/invalid ranges rejected with the standard error contract.
- Backend-authoritative server-side aggregation only (no client-side arithmetic of authoritative totals; no decorative chart library).
- OWNER + STAFF read access, anonymous 401, no mutation endpoints.
- Aggregation-correctness and RBAC tests, full regression, frontend lint/typecheck/build.
- Documentation (this report) per `docs/phase-14/10_PHASE_14_DELIVERABLES.md`.

Out of scope (per scope + deferred docs): accounting automation, double-entry, GST automation, payment gateways, bank/cloud-accounting integration, payroll/settlement behavior changes, new payment/invoice types, WhatsApp/SMS reminders, and export/PDF.

## 3. Implementation Summary

**Confirmed design decision:** the reports API is a thin aggregation endpoint — `GET /api/v1/reports/summary/` — that computes every figure on the fly from existing authoritative records. No new models, no new tables, no new financial records. Income and expenses are pulled straight from the same service functions the income and expense pages use, and the net position is `income − expenses` computed server-side. Workload and active counts are live shop snapshots with the same semantics as the dashboard; everything date-based is filtered by the inclusive range.

- `apps/finance/services.py` gains `build_reports_summary(date_from, date_to)` which assembles `orders`, `customers`, `tailors` and `financial` sections, reusing `build_income_summary`, `build_expense_summary`, `_range_kwargs`, `_decimal_sum` and `_workload_totals`.
- `apps/finance/views.py` gains `ReportsSummaryView` (`IsOwnerOrStaff`, GET-only), reusing the standard `_parse_range` validation.
- The frontend replaces the Reports placeholder with a real page wired through a new `useReportsSummary` React Query hook; query keys are invalidated by every mutation that changes report data (payments/refunds, expenses, orders, work assignments, payroll payments, salary advances).

## 4. Backend Changes

- `backend/apps/finance/services.py`
  - New `build_reports_summary(date_from=None, date_to=None)` returning:
    - `range` — the applied `date_from` / `date_to`.
    - `orders` — `total`, `status_distribution` (every `OrderStatus` key plus `total`, aggregated with `Count`), `revenue` (`Sum` of `Order.total_amount` in range), `garment_quantities` (`{SHIRT: n, PANT: n}` via `OrderItem` summed in range).
    - `customers` — `active_customers` (live), `new_customers` (created within range), `customers_with_orders` (distinct customers with an order in range).
    - `tailors` — `active_tailors` (live) and `workload` from the shared `_workload_totals()` (assigned / completed / outstanding / earned).
    - `financial` — `income` (from `build_income_summary`, minus the `success` flag), `expenses` (from `build_expense_summary`, minus `success`), `net_position` (`income − expenses`, rounded 2dp), `payroll_paid` (`PayrollPayment.amount` summed by `payment_date`), `salary_advances` (`SalaryAdvance.amount` summed by `advance_date`), `order_revenue` (same sum as `orders.revenue`).
  - Module docstring extended to describe the reports layer (Phase 14).
  - Filter semantics: orders by `order_date`, customers by `created_at__date`, payments/refunds by `payment_date`, expenses by `expense_date`, payroll by `payment_date`, advances by `advance_date`; all via the existing `_range_kwargs` helper. Workload and active counts are not date-filtered.
  - black/isort formatted.
- `backend/apps/finance/views.py`
  - New `ReportsSummaryView(APIView)` with `permission_classes = [IsOwnerOrStaff]` and GET-only; validates `date_from` / `date_to` with the existing `_parse_range` (invalid dates and reversed ranges → 400 with the standard error contract).
- `backend/apps/finance/urls.py`
  - New route `reports/summary/` → `ReportsSummaryView` (name `reports-summary`), under the same `IsOwnerOrStaff`-gated finance router area. Endpoint: `GET /api/v1/reports/summary/`.
- `backend/apps/finance/tests/helpers.py`
  - Added `reports_summary_url()` → `/api/v1/reports/summary/`.

## 5. Frontend Changes

- `frontend/src/types/reports.ts` (new)
  - `ReportsSummary`, `ReportOrders`, `ReportOrderCounts`, `ReportCustomers`, `ReportTailors`, `ReportWorkload`, `ReportFinancial`, plus `ReportIncome` / `ReportExpenses` (income/expense shapes without the `success` flag, since the backend pops it) and `ReportsSummaryParams`. Reuses `ORDER_STATUSES`-style status keys and the income/expense row types from `types/finance`.
- `frontend/src/services/financeService.ts`
  - Added `getReportsSummary(params)` → `GET /reports/summary/` (with the existing `buildQuery` helper).
- `frontend/src/hooks/useReports.ts` (new)
  - Exports `REPORTS_KEY` and `useReportsSummary(params)` React Query hook.
- `frontend/src/pages/Reports.tsx` (new, replaces the placeholder)
  - Breadcrumbs + header; From / To / Apply / Reset date filter (apply is explicit, reset clears both); range chip ("All time" or "X to Y").
  - Financial stat cards: Net Position (green/red by sign), Income (payments/refunds sublabel), Expenses, Order Revenue.
  - Operational section cards: Orders (total, status-distribution chips using the existing `ORDER_STATUS_COLORS`, garment-quantity chips), Customers (active / new / with orders), Tailor Workload (active tailors, assigned / completed / outstanding pieces, earnings), Payroll & Settlements (payroll paid, salary advances).
  - Breakdown tables: Income by Payment Type (refund rows in red) and Expenses by Category — reusing `PAYMENT_TYPE_LABELS` / `EXPENSE_CATEGORY_LABELS`.
  - Loading spinner, `LinearProgress` refetch indicator, error `Alert` + Retry, and empty states per table/card; no decorative charts (no chart dependency added).
- `frontend/src/routes/AppRoutes.tsx`
  - `/reports` now routes to the real `Reports` page (import moved out of `Placeholders`).
- Cache invalidation — the report query is invalidated (`[REPORTS_KEY]`) on every mutation that changes report figures:
  - `useFinance.ts` — `useCreateExpense`.
  - `useInvoices.ts` — `useCreatePayment`, `useCreateInvoice`, `useCreateOrderInvoice`.
  - `useOrders.ts` — `useCreateOrder`, `useUpdateOrder`, `useChangeOrderStatus`.
  - `useTailors.ts` — `useCreateWorkAssignment`, `useUpdateWorkAssignment`, `useChangeWorkAssignmentStatus`.
  - `usePayroll.ts` — `useRecordPayment`, `useSettleEntry`, `useApplyAdvanceToEntry`.
  - `useAdvances.ts` — `useCreateAdvance`.

## 6. Database Changes

**None.** `python manage.py makemigrations --check --dry-run` → `No changes detected`.

- No schema or data migration; no new models or tables.
- All aggregations reuse the existing indexes and the authoritative tables from prior phases (orders, customers, tailors/work assignments, billing `CustomerPayment`, expenses, `PayrollPayment`, `SalaryAdvance`).

## 7. API Changes

All under `/api/v1/`. Errors use the standard `{success:false, error:{code, message, details?}}` contract.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/reports/summary/` | OWNER + STAFF | Read-only business-insights summary with optional inclusive `date_from` / `date_to` |

Example response (trimmed):

```json
{
  "success": true,
  "range": {"date_from": "2026-01-01", "date_to": "2026-01-31"},
  "orders": {
    "total": 12,
    "status_distribution": {"total": 12, "NEW": 3, "CUTTING": 2, "STITCHING": 4, "READY": 1, "COLLECTED": 2, "CANCELLED": 0},
    "revenue": 4200.0,
    "garment_quantities": {"SHIRT": 15, "PANT": 8}
  },
  "customers": {"active_customers": 40, "new_customers": 5, "customers_with_orders": 9},
  "tailors": {"active_tailors": 6, "workload": {"assigned_quantity": 23, "completed_quantity": 12, "outstanding_quantity": 11, "earned_amount": 1560.0}},
  "financial": {
    "income": {"total_income": 3800.0, "payment_count": 11, "refund_count": 1, "total_refunds": 200.0, "by_payment_method": [...], "by_payment_type": [...]},
    "expenses": {"total_expenses": 1500.0, "expense_count": 6, "by_category": [...], "by_payment_method": [...]},
    "net_position": 2300.0,
    "payroll_paid": 8000.0,
    "salary_advances": 500.0,
    "order_revenue": 4200.0
  }
}
```

- Inclusive `date_from` / `date_to` boundaries; invalid dates → 400; `date_from > date_to` → 400; both optional (omitted → all time).
- No mutation routes (GET only → POST/PUT/PATCH/DELETE → 405).
- `COERCE_DECIMAL_TO_STRING=False` — Decimal fields serialize as numbers.

## 8. RBAC

Backend-enforced, consistent with prior phases:

- `ReportsSummaryView` → `IsOwnerOrStaff`: anonymous → 401; OWNER and STAFF both read → 200; GET only (no create/update/delete surface).
- Verified by integration tests: anonymous → 401; OWNER → 200; STAFF → 200; POST/PUT/PATCH/DELETE → 405; reads never mutate data.
- The frontend has no mutation controls on the Reports page; authoritative totals are always server-computed.

## 9. Testing Results

Backend (all pass, executed from `backend/` with the project venv):

```text
python manage.py check                            -> System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run -> No changes detected
python -m pytest apps/finance                     -> 97 passed in 46.92s (72 prior + 25 new)
python -m pytest (full suite)                     -> 514 passed in 227.02s (baseline 489 + 25 new)
python -m black --check apps/finance              -> clean
python -m isort --check-only apps/finance         -> clean
```

New tests — `backend/apps/finance/tests/test_reports.py` (25 tests):

- **Auth/RBAC**: anonymous 401; OWNER and STAFF read 200; POST/PUT/PATCH/DELETE → 405.
- **Orders**: empty-state shape; count + status distribution vs DB; revenue equals DB `Sum`; garment quantities (`{SHIRT, PANT}`) vs DB; `order_date` filtering inclusive.
- **Customers**: `active_customers`, `new_customers`, `customers_with_orders` match direct DB counts (archived customers counted as inactive, not orderable).
- **Tailors**: workload block equals the shared `_workload_totals()` helper output (assigned / completed / outstanding / earned).
- **Financial consistency**: report income equals `build_income_summary(...)` and expenses equals `build_expense_summary(...)` (the authoritative sources, so the reports can never disagree with the income/expense pages); refunds reduce income and never produce positive income; net position = income − expenses; `payroll_paid` from `PayrollPayment.payment_date`; `salary_advances` from `SalaryAdvance.advance_date`.
- **Filters**: no-filter (all records), `date_from` only, `date_to` only, combined, inclusive boundaries; invalid date → 400; reversed range → 400.
- Test helpers used from the billing / customers / payments / tailors modules (invoice + customer payment, order creation via active customers, finalized payroll entries, advances, work assignments), so the fixtures exercise the real module constraints.

Frontend (all pass):

```text
npm run lint  -> clean
npx tsc --noEmit -> clean
npm run build -> clean (tsc + vite build; pre-existing chunk-size warning only)
```

## 10. Manual Verification

Phase 14 manual verification is checklist-only per `docs/phase-14/08_PHASE_14_MANUAL_VERIFICATION.md` and remains **NOT STARTED**. The Phase 14 flows (reports summaries matching the income/expense/dashboard figures, all date filters, RBAC split, no-mutation guarantee) are exercised end-to-end by the integration tests through the real URL routes with the DRF test client. Frontend behavior is covered by the static build checks; the UI follows the proven vertical-slice pattern and mirrors backend validation (backend remains authoritative).

## 11. Documentation

- `docs/phase-14/` — the ten planning/specification documents, this report, and the manual-verification checklist (left `NOT STARTED`).
- `README.md` — stage line updated to Phase 14, new `## 8.6 Reports & Business Insights (Phase 14)` section, and phase-status list updated (`Phase 14 — Reports & Business Insights: complete`, `Phase 15+ — pending`).

## 12. Files Changed

**Modified - backend:**
- `backend/apps/finance/services.py` — `build_reports_summary`, docstring
- `backend/apps/finance/views.py` — `ReportsSummaryView`
- `backend/apps/finance/urls.py` — `reports/summary/` route
- `backend/apps/finance/tests/helpers.py` — `reports_summary_url`

**Created - backend:**
- `backend/apps/finance/tests/test_reports.py`

**Created - frontend:**
- `frontend/src/types/reports.ts`
- `frontend/src/hooks/useReports.ts`
- `frontend/src/pages/Reports.tsx`

**Modified - frontend:**
- `frontend/src/services/financeService.ts` — `getReportsSummary`
- `frontend/src/routes/AppRoutes.tsx` — real Reports page for `/reports`
- `frontend/src/hooks/useFinance.ts`, `useInvoices.ts`, `useOrders.ts`, `useTailors.ts`, `usePayroll.ts`, `useAdvances.ts` — `REPORTS_KEY` invalidation

**Documentation:**
- `docs/phase-14/` planning/spec documents and this report; `README.md` updates

## 13. Known Issues

- Frontend production build emits a pre-existing chunk-size warning (>500 kB after minification); non-blocking and unchanged by this phase.
- Workload and active counts are live shop snapshots (not date-filtered), by design, matching the dashboard semantics; only explicitly date-based metrics are scoped by the range.
- DRF's `COERCE_DECIMAL_TO_STRING=False` means API JSON returns Decimal fields as numbers; Django/DB values remain `Decimal`, and tests assert accordingly.

## 14. Deferred Items

Explicitly out of scope for Phase 14 (per `docs/phase-14/01_PHASE_14_SCOPE.md` and `09_PHASE_14_DEFERRED_AND_GUARDRAILS.md`) and not implemented: accounting automation, double-entry accounting, GST automation, payment gateways, bank/cloud-accounting integration, payroll/settlement behavior changes, new payment/invoice types, WhatsApp/SMS reminders, and report export / PDF generation. These remain future-phase candidates.

## 15. Git Verification

The Phase 14 changes are present in the working tree but **no commit was created** (commits are only made on explicit request). The working tree also still contains the uncommitted Phase 12/13 work and other pre-existing uncommitted files from earlier phases (documented in the Phase 13 report), which were left undisturbed. Phase 14 additions: `backend/apps/finance/tests/test_reports.py`, `frontend/src/types/reports.ts`, `frontend/src/hooks/useReports.ts`, `frontend/src/pages/Reports.tsx`, `docs/phase-14/` (planning docs + this report), plus modifications to the finance service/views/urls/tests/helpers, `financeService.ts`, `AppRoutes.tsx`, and the six mutation hook files listed above. `README.md` was updated. The added/modified sets were verified against the diff before reporting completion.

## 16. Phase 15 Readiness

**Ready. Phase 14 is PASS and ready for Phase 15.**

- Reports derive entirely from the authoritative existing modules; no duplicate financial system exists (income and expense figures are the exact same aggregations the income/expense pages use).
- Backend RBAC enforced (reports read-only; anonymous 401; OWNER/STAFF read; no mutations).
- Full 514-test suite passes; backend gates clean (check, makemigrations --check, black, isort); frontend static checks clean (lint, TypeScript, build).
- Manual verification checklist remains `NOT STARTED` until actually performed.
