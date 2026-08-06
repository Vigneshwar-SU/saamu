# Phase 13 Completion Report

## 1. Status

Status: **PASS**

Phase 13 (Income Management — customer-payment-derived income) is complete. It repurposes the Phase 8 income surface of `backend/apps/finance/` to be **derived, read-only, and refund-aware**: the income API no longer records manual income entries but reads from the authoritative `CustomerPayment` records produced by the Phase 11 billing app. Income, the new income summary endpoint and the dashboard all aggregate through one shared service function, so the figures can never disagree.

**Final status:** Phase 13 is **PASS and ready for Phase 14**.

## 2. Scope

Per `docs/phase-13/01_PHASE_13_SCOPE.md`, the phase delivers:

- A shared income aggregation service over customer payments (gross − refunds).
- A read-only income API (`GET /api/v1/income/`, `GET /api/v1/income/{id}/`).
- A new income summary API (`GET /api/v1/income/summary/`) with payment-method and payment-type breakdowns.
- Required filters (`date_from`, `date_to`, `payment_method`, `payment_type`), all validated.
- Refund-aware net calculations (refunds reduce net income; a refund is never positive income).
- Reusable aggregation logic (no client-side arithmetic, no duplicated queries).
- Automated backend tests covering the list, summary and dashboard equivalence.
- Frontend vertical slice: income types, service call, React Query hooks, and a rewritten read-only Income page with summary cards, filters and breakdown tables, plus a `recent_payments` dashboard update.
- Documentation (this report) per `docs/phase-13/10_PHASE_13_DELIVERABLES.md`.

## 3. Implementation Summary

**Confirmed design decision:** income = customer payments only. The manual `Income` model is retained in the database as a legacy table (no migration, no drop) but is no longer written to or read by the application. The STAFF "Add Income" path is removed; income entries are created exclusively by recording customer payments / refunds in the billing app (Phase 11, STAFF-only). OWNER and STAFF are both read-only on income.

The implementation is a thin, non-invasive layer over the existing ledger app:

- `apps/finance/services.py` exposes `build_income_summary(...)`, the single aggregation entry point used by both the income summary API and the dashboard's `financial.recorded_income`. A `_income_filters` helper centralizes the shared, validated filter logic for the list, detail and summary views.
- `apps/finance/serializers.py` redefines `IncomeSerializer` as a read-only `CustomerPayment` serializer, so the income list and the dashboard's `recent_payments` rows are serialized from the same payment model with refund-aware `net_amount`.
- `apps/finance/views.py` converts `IncomeViewSet` to a `ReadOnlyModelViewSet` (list / detail / `summary` action) with `_apply_list_filters`.
- The frontend income surface is rewritten to be read-only: summary stat cards, filters, a payment-detail table and two breakdown tables. Dashboard "Recent Income" now renders payment rows. The obsolete `IncomeFormDialog` is deleted and all income-creation hooks/service calls are removed. Payment mutations keep living in the billing hooks, which now also invalidate the income queries.

## 4. Backend Changes

- `backend/apps/finance/services.py`
  - New `build_income_summary(date_from, date_to, payment_method=None, payment_type=None)` returning `success`, `total_income` (gross − refunds, `Decimal` rounded to 2 places), `payment_count`, `refund_count`, `total_refunds`, `by_payment_method[]` and `by_payment_type[]` (each row: code, `_display` label, net `total` — negative for REFUND — and `count`). Net income per payment uses `Case(When(payment_type=REFUND, then=-F("amount")), default=F("amount"), output_field=DecimalField(max_digits=12, decimal_places=2))`.
  - New internal `_income_filters(date_from, date_to, payment_method=None, payment_type=None)` helper; filters are `Q`-based with validated method/type values.
  - Dashboard integration: `financial.recorded_income` now calls `build_income_summary(date_from, date_to)["total_income"]`; `recent_income` renamed `recent_payments` (latest 5 `CustomerPayment` rows with `select_related("invoice__order__customer", "recorded_by")`, serialized with `IncomeSerializer`).
  - `Income` imports removed; `CustomerPayment` and the aggregation imports added; module docstring updated; black/isort formatted.
- `backend/apps/finance/serializers.py`
  - `IncomeSerializer` rewritten as a read-only `CustomerPayment` ModelSerializer (`read_only_fields` covering every field). Fields: `id`, `payment_type`, `payment_type_display`, `payment_method`, `payment_method_display`, `amount`, `net_amount` (SerializerMethodField: REFUND → −amount), `payment_date`, `invoice_number` (source `invoice.invoice_number`), `order_number` (source `invoice.order.order_number`), `customer_name` (source `invoice.order.customer.full_name`), `reference`, `notes`, `recorded_by`, `recorded_by_name` (SerializerMethodField), `created_at`.
  - `Decimal` import retained for `ExpenseSerializer`.
- `backend/apps/finance/views.py`
  - `IncomeViewSet` is now `ReadOnlyModelViewSet`; queryset `CustomerPayment.objects.select_related("invoice__order__customer", "recorded_by")`; `_apply_list_filters` validates `payment_method` against `CustomerPayment.Method.values` and `payment_type` against `CustomerPayment.PaymentType.values` (invalid values → 400 `ValidationError` `{"payment_method": "Invalid payment method filter."}` / `{"payment_type": "Invalid payment type filter."}`).
  - New `summary` action (`GET /api/v1/income/summary/`) returning `build_income_summary(...)` with the same validated filters.
  - Module docstring updated; black/isort formatted.
- `backend/apps/finance/admin.py` and `backend/apps/finance/models.py` — untouched in this phase (the legacy `Income` model/table and its admin remain in place unchanged; no migration produced).

## 5. Frontend Changes

- `frontend/src/types/finance.ts`
  - Removed `INCOME_CATEGORIES`, `IncomeCategory`, `INCOME_CATEGORY_LABELS`, and `IncomePayload` (manual income creation is gone).
  - Re-exports `PAYMENT_TYPES`, `PAYMENT_TYPE_LABELS` and `type PaymentType` from `./billing` (single source; the duplicate set was removed from finance.ts) and imports `PaymentType` for local use.
  - `Income` rewritten to the payment shape: `id`, `payment_type`, `payment_type_display`, `payment_method`, `payment_method_display`, `amount`, `net_amount`, `payment_date`, `invoice_number`, `order_number`, `customer_name`, `reference`, `notes`, `recorded_by`, `recorded_by_name`, `created_at` (no `updated_at`).
  - `IncomeListParams` replaces `category` with `payment_method?: PaymentMethod | ''` and `payment_type?: PaymentType | ''`.
  - Added `IncomeSummary`, `IncomeSummaryMethod`, `IncomeSummaryType`, `IncomeSummaryParams`.
  - `DashboardSummary.recent_income` → `recent_payments: Income[]`.
- `frontend/src/services/financeService.ts`
  - Removed `createIncome`; added `getIncomeSummary(params)` → `GET /income/summary/`.
- `frontend/src/hooks/useFinance.ts`
  - Rewritten: exports `INCOME_KEY`, `INCOME_SUMMARY_KEY`, `EXPENSES_KEY`, `EXPENSE_SUMMARY_KEY`, `DASHBOARD_KEY`; hooks `useIncomeList`, `useIncomeSummary`, `useExpenseList`, `useExpenseSummary`, `useCreateExpense`, `useDashboardSummary`. `useCreateIncome` removed.
- `frontend/src/hooks/useInvoices.ts`
  - Imports `INCOME_KEY`, `INCOME_SUMMARY_KEY`, `DASHBOARD_KEY` from `./useFinance`; `useCreatePayment` onSuccess now invalidates the income list, income summary and dashboard queries in addition to invoices.
- `frontend/src/pages/Income.tsx`
  - Rewritten read-only page for both roles: three summary stat cards (Total Income net, Payments count, Refunds total + count) from `useIncomeSummary(filterParams)`; filters (date from/to, payment method, payment type); a table with Date, payment-type Chip (green for income, red for REFUND), Method, Amount (net, red for REFUND), Customer, Invoice, Recorded By; pagination; and two breakdown tables (Income by Payment Method, Income by Payment Type). Loading/error/empty states follow the existing page patterns.
- `frontend/src/pages/Dashboard.tsx`
  - "Recent Income" now renders `recent_payments` (Date, payment-type chip, `net_amount` color-coded for refunds); "Recorded Income" sublabel updated; the shared `categoryLabel` helper was split into `expenseCategoryLabel` (income categories no longer exist).
- `frontend/src/components/IncomeFormDialog.tsx` — deleted (no longer imported anywhere).

## 6. Database Changes

**None.** `python manage.py makemigrations --check --dry-run` → `No changes detected`.

- No schema or data migration.
- The manual `Income` model and its table remain in the database as legacy (deliberately retained, never written or read by the application; documented decision).
- `CustomerPayment` (Phase 11) is the authoritative source; its indexes are reused for the income date/method/type filters.

## 7. API Changes

All under `/api/v1/`. Errors use the standard `{success:false, error:{code, message, details?}}` contract.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/income/` | OWNER + STAFF | Read-only list of customer payments (date_from / date_to / payment_method / payment_type filters, paginated 20) |
| GET | `/income/{id}/` | OWNER + STAFF | Payment detail in income shape |
| GET | `/income/summary/` | OWNER + STAFF | Server-side `total_income`, `payment_count`, `refund_count`, `total_refunds`, `by_payment_method`, `by_payment_type` (same filters) |
| ~~POST~~ | ~~`/income/`~~ | — | Removed — income is no longer created manually; payments/refunds are recorded through the Phase 11 billing API |
| GET | `/dashboard/summary/` | OWNER + STAFF | Existing Phase 8 dashboard; `financial.recorded_income` now equals the income summary total; `recent_income` → `recent_payments` |

Example summary response:

```json
{
  "success": true,
  "total_income": 1200.0,
  "payment_count": 3,
  "refund_count": 1,
  "total_refunds": 300.0,
  "by_payment_method": [
    {"payment_method": "CASH", "payment_method_display": "Cash", "total": 1200.0, "count": 4}
  ],
  "by_payment_type": [
    {"payment_type": "ADVANCE", "payment_type_display": "Advance", "total": 1000.0, "count": 1},
    {"payment_type": "PARTIAL", "payment_type_display": "Partial", "total": 500.0, "count": 1},
    {"payment_type": "FINAL", "payment_type_display": "Final", "total": 0.0, "count": 0}
  ]
}
```

- Inclusive `date_from` / `date_to` boundaries; invalid dates → 400; invalid `payment_method` / `payment_type` filter values → 400.
- No update/delete routes (the viewset is read-only; POST/PUT/PATCH/DELETE → 405).
- `COERCE_DECIMAL_TO_STRING=False` — Decimal fields serialize as numbers.

## 8. RBAC

Backend-enforced, unchanged in shape from prior phases:

- `IncomeViewSet` — read-only endpoints (`list`, `retrieve`, `summary`) → `IsOwnerOrStaff`; no mutation actions exist.
- Payment/refund recording remains the responsibility of the Phase 11 billing app (`IsStaffRole`, STAFF only, `recorded_by` server-side).
- Verified by integration tests: anonymous list/summary → 401; OWNER list/detail/summary → 200 (and no create surface); STAFF list/detail/summary → 200; POST/PUT/PATCH/DELETE → 405; reads never mutate payments.

## 9. Testing Results

Backend (all pass, executed from `backend/` with the project venv — Python 3.12.6, Django 5.2.16, pytest 9.1.1):

```text
python manage.py check                            -> System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run -> No changes detected
python -m pytest apps/finance                     -> 72 passed in 35.01s
python -m pytest (full suite)                     -> 489 passed in 216.55s (baseline 470 + 19 new)
python -m black --check apps/finance              -> clean (15 files unchanged, 1 skipped)
python -m isort --check-only apps/finance         -> clean
```

New/updated tests:

- `apps/finance/tests/test_income.py` (rewritten) — anonymous 401 on list/summary; OWNER + STAFF read list/detail; payment detail fields (type/method displays, invoice/order/customer names, reference, notes); refund row serialized with negative `net_amount` (₹1000 FINAL + ₹300 REFUND → 2 rows); read-only endpoint (POST/PUT/PATCH/DELETE → 405); reads never mutate payments; date-range filtering with inclusive boundaries; payment-method and payment-type filters plus invalid-value 400s; combined filters; invalid date 400s; pagination.
- `apps/finance/tests/test_income_summary.py` (new, 20 tests) — anonymous denied; OWNER/STAFF read; empty state zeros; single payment counted once; multi-payment aggregation; partial refund math (1000 + 500 − 300 = 1200); full refund → zero net; refunds never produce positive income; date-range / method / type / combined filters; invalid filters → 400; by-method and by-type row totals sum to `total_income`; summary equals a direct DB aggregation; dashboard `recorded_income` equals the income summary total.
- `apps/finance/tests/test_dashboard.py` (updated) — fixtures switched from manual income creation to `create_invoice` + `create_customer_payment` (billing helpers); `recent_payments` assertions; order-revenue test reuses the order via `create_invoice(order)` so shared fixtures are not double-counted; active-counts test keeps the customer count stable.
- `apps/finance/tests/helpers.py` — `income_summary_url()` added; `create_income` removed.

Frontend (all pass):

```text
npm run lint    -> clean
npm run build   -> clean (tsc + vite build; pre-existing chunk-size warning only)
```

## 10. Manual Verification

Phase 13 manual verification is checklist-only per `docs/phase-13/08_PHASE_13_MANUAL_VERIFICATION.md` and remains **NOT STARTED**. The Phase 13 flows (payments/refunds appearing in income, list/detail/summary, all filters, refund-aware net math, RBAC split, dashboard equivalence) are exercised end-to-end by the integration tests through the real URL routes with the DRF test client. Frontend behavior is covered by the static build checks; the UI follows the proven vertical-slice pattern and mirrors backend validation (backend remains authoritative).

## 11. Documentation

- `docs/phase-13/` — the ten planning/specification documents, this report, and the manual-verification checklist (left `NOT STARTED`).
- `README.md` — stage line, income/expense section (`## 8.3`) and phase-status list updated for Phase 13.

## 12. Files Changed

**Modified - backend:**
- `backend/apps/finance/services.py` — `build_income_summary`, `_income_filters`, dashboard repointed, `recent_payments`
- `backend/apps/finance/serializers.py` — read-only `CustomerPayment`-based `IncomeSerializer`
- `backend/apps/finance/views.py` — read-only `IncomeViewSet` + `summary` action + filter validation
- `backend/apps/finance/tests/helpers.py` — `income_summary_url`, `create_income` removed
- `backend/apps/finance/tests/test_dashboard.py` — payment-derived fixtures, `recent_payments`
- `backend/apps/finance/tests/test_income.py` — rewritten for payment-derived income

**Created - backend:**
- `backend/apps/finance/tests/test_income_summary.py`

**Modified - frontend:**
- `frontend/src/types/finance.ts` — payment-derived `Income`, `IncomeSummary*`, filters, billing re-exports
- `frontend/src/services/financeService.ts` — `getIncomeSummary`, `createIncome` removed
- `frontend/src/hooks/useFinance.ts` — exported query keys, `useIncomeSummary`, `useCreateIncome` removed
- `frontend/src/hooks/useInvoices.ts` — income/dashboard invalidation in `useCreatePayment`
- `frontend/src/pages/Income.tsx` — rewritten read-only page (summary cards, filters, table, breakdowns)
- `frontend/src/pages/Dashboard.tsx` — `recent_payments` recent-income table

**Deleted - frontend:**
- `frontend/src/components/IncomeFormDialog.tsx`

**Documentation:**
- `docs/phase-13/` planning/spec documents and this report; `README.md` updates

## 13. Known Issues

- Frontend production build emits a pre-existing chunk-size warning (>500 kB after minification); non-blocking.
- The manual `Income` model/table remains in the database as legacy (never read or written by the application). A future phase may remove it via an explicit migration if desired.
- DRF's `COERCE_DECIMAL_TO_STRING=False` means API JSON returns Decimal fields as numbers; Django/DB values remain `Decimal`, and tests assert accordingly.

## 14. Deferred Items

Explicitly out of scope for Phase 13 (per `docs/phase-13/01_PHASE_13_SCOPE.md` and `09_PHASE_13_DEFERRED_AND_GUARDRAILS.md`) and not implemented: physical removal of the legacy `Income` table, income export/reports, GST automation, payment gateways, double-entry accounting, automatic income-accounting integration with banks/cloud accounting, WhatsApp/SMS reminders, and any new STAFF mutation surface for income (income stays derived from billing).

## 15. Git Verification

The Phase 13 changes are present in the working tree but **no commit was created** (commits are only made on explicit request). `git status` shows the Phase 13 modifications plus the pre-existing uncommitted work-tree files from earlier phases (tailors work-assignments test, tailor/order/assign-work UI files, `ReportProgressDialog`, `WorkAssignmentStatusChip`, etc.) which were left undisturbed. Untracked additions for this phase are `backend/apps/finance/tests/test_income_summary.py` and `docs/phase-13/`; `frontend/src/components/IncomeFormDialog.tsx` is staged for deletion. The deleted-file and added-file sets were verified against the diff before reporting completion.

## 16. Phase 14 Readiness

**Ready. Phase 13 is PASS and ready for Phase 14.**

- Income is derived entirely from actual customer payments; refunds reduce net income; no duplicate financial system exists.
- Backend RBAC enforced (income read-only; payment mutations STAFF-only through the billing app).
- Full 489-test suite passes; backend gates clean (check, makemigrations --check, black, isort); frontend static checks clean (lint, TypeScript, build).
- Phase 11 billing, Phase 12 expenses and the Phase 8 ledger remain green and untouched in behavior.
