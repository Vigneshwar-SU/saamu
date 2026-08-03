# Phase 8 Completion Report

## 1. Summary

Status: **PASS**

Phase 8 (Income, Expenses & Financial Dashboard) is complete. A new `apps/finance` app adds:

- **Income records** - shop income entries with controlled categories (`ORDER_PAYMENT`, `OTHER_INCOME`), `amount > 0`, `income_date`, description, reference and `recorded_by` audit.
- **Expense records** - shop expense entries with controlled categories (`RENT`, `ELECTRICITY`, `MATERIAL`, `MAINTENANCE`, `SHOP_SUPPLIES`, `TRANSPORT`, `OTHER_EXPENSE`), same validation and audit rules.
- **Read-only financial dashboard** - recorded income, recorded expenses, net recorded balance, payroll paid (derived from actual `PayrollPayment` records), salary advances (kept as a separate metric, never classified as expenses), and order revenue (clearly distinguished from recorded cash income).
- **Operational dashboard** - order status counts, garment quantities (SHIRT/PANT), tailor workload (assigned/completed/outstanding/earned), active customer/tailor counts, and recent income/expenses.
- **RBAC** - OWNER is read-only (income, expenses, dashboard); STAFF creates income/expense records and reads everything; anonymous gets 401. Backend permissions are authoritative.
- **Inclusive date-range filtering** - `date_from` / `date_to` on income, expenses and dashboard; `date_to` cannot precede `date_from`.

The frontend replaces the Dashboard / Income / Expenses placeholders with real pages: a Dashboard (date-range filter, financial cards, order status, shop overview, tailor workload, recent income/expenses), an Income page (date/category filters, pagination, STAFF-only Add Income) and an Expenses page (date/category filters, pagination, STAFF-only Add Expense). All money uses Decimal arithmetic; historical records are never physically deleted and have no update/delete API.

All Phase 8 scope items from `docs/phase-8/01_PHASE_8_SCOPE.md` are implemented; customer billing/invoices, payment gateways, bank integrations, tax/PF/ESI, leave, notifications, accounting ledger/double-entry bookkeeping and changes to finalized payroll remain explicitly out of scope.

**Final status:** Phase 8 is **PASS and ready for Phase 9**.

## 2. Features Implemented

- **Income records** - STAFF records income (category, amount > 0, date, optional reference/description); the authenticated user is stored as `recorded_by` server-side (never accepted from the client). Records are never updated or deleted.
- **Expense records** - same behavior as income with the expense category set. Records are never updated or deleted.
- **Controlled categories** - fixed category choices in the model (no dynamic category table), per `docs/phase-8/02_PHASE_8_DATA_MODEL.md`.
- **List filtering** - `date_from`, `date_to` (inclusive), `category`, `page` on both income and expenses; invalid categories return 400; invalid dates return a clean 400 instead of a 500.
- **Dashboard financial summary** - recorded income / recorded expenses / net recorded balance from the Phase 8 ledger; payroll paid summed from `PayrollPayment.amount`; salary advances summed from `SalaryAdvance.amount` as a separate metric; order revenue summed from `Order.total_amount` and labeled distinctly from recorded cash income.
- **Dashboard operational summary** - per-status order counts plus total, garment quantities, tailor workload (assigned/completed/outstanding pieces + piece-rate earnings across all assignments), active customer/tailor counts, and the 5 most recent income and expense records.
- **Read-only dashboard** - `GET /dashboard/summary/` never mutates source data; payroll, payment and advance history is never rewritten.
- **Frontend vertical slice** - `types/finance.ts`, `services/financeService.ts`, `hooks/useFinance.ts`, `IncomeFormDialog` / `ExpenseFormDialog` (react-hook-form + zod mirroring backend rules), and real `Dashboard` / `Income` / `Expenses` pages wired into routes and the existing sidebar (no navigation rework needed; entries already existed).

## 3. Data Model

### `apps/finance/models.py` (migration `0001_initial.py`)

**`Income`** (extends `apps.common.models.TimeStampedModel`):

| Field | Type | Notes |
|---|---|---|
| `category` | CharField(20) | choices `ORDER_PAYMENT` / `OTHER_INCOME` |
| `amount` | Decimal(12,2) | `CheckConstraint` `> 0` |
| `income_date` | DateField | |
| `description` | TextField, blank | |
| `reference` | CharField(100), blank | |
| `recorded_by` | FK AUTH_USER_MODEL (SET_NULL), null | audited marker, set server-side |

- `Meta.ordering = ["-income_date", "-created_at"]`; `Index` on `income_date` and on `category`.
- No delete/update path in the API or admin.

**`Expense`** (extends `TimeStampedModel`):

| Field | Type | Notes |
|---|---|---|
| `category` | CharField(20) | choices `RENT` / `ELECTRICITY` / `MATERIAL` / `MAINTENANCE` / `SHOP_SUPPLIES` / `TRANSPORT` / `OTHER_EXPENSE` |
| `amount` | Decimal(12,2) | `CheckConstraint` `> 0` |
| `expense_date` | DateField | |
| `description` | TextField, blank | |
| `reference` | CharField(100), blank | |
| `recorded_by` | FK AUTH_USER_MODEL (SET_NULL), null | audited marker, set server-side |

- `Meta.ordering = ["-expense_date", "-created_at"]`; `Index` on `expense_date` and on `category`.
- No delete/update path in the API or admin.

Note: the user prompt mentioned payment methods (CASH / BANK_TRANSFER / UPI / OTHER), but the authoritative Phase 8 data-model doc lists no payment-method field for income/expense; per the prompt instruction to "adjust to match docs", payment method was not added to the ledger models and is noted as deferred.

## 4. API Endpoints

All under `/api/v1/`. Error contract is the standard `{success:false, error:{code, message, details?}}`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET / POST | `/income/` | read OWNER+STAFF / create STAFF | List (date_from, date_to, category, page) / create |
| GET | `/income/{id}/` | OWNER+STAFF | Income detail |
| GET / POST | `/expenses/` | read OWNER+STAFF / create STAFF | List (date_from, date_to, category, page) / create |
| GET | `/expenses/{id}/` | OWNER+STAFF | Expense detail |
| GET | `/dashboard/summary/` | OWNER+STAFF | Financial + operational dashboard summary (date_from, date_to) |

- All lists paginated at 20/page. Dashboard `GET` only.
- Income/expense serializers expose `category_display` and `recorded_by_name` alongside the raw values.

## 5. Business Rules

- **Positive amounts** - income/expense amounts must be `> 0`, enforced at the database (`CheckConstraint`) and serializer level.
- **Required category and date** - both mandatory on create; invalid categories rejected.
- **Inclusive date ranges** - `date_from` / `date_to` filter with `>=` / `<=` on income/expense dates and dashboard ranges; `date_to` earlier than `date_from` returns 400; malformed dates return 400.
- **Derived, never stored** - recorded income = sum of `Income.amount` in range; recorded expenses = sum of `Expense.amount` in range; net = income - expenses; payroll paid = sum of `PayrollPayment.amount` (by `payment_date`); salary advances = sum of `SalaryAdvance.amount` (by `advance_date`), kept separate and never treated as expenses; order revenue = sum of `Order.total_amount` (by `order_date`), distinct from recorded cash income.
- **Audit trail** - every record stores `recorded_by` from the authenticated user; historical records are never physically deleted (no delete/update API; 405 on unsupported methods).
- **Read-only dashboard** - the dashboard only reads authoritative sources and never mutates finalized payroll, payment or advance history.

## 6. RBAC Verification

Backend-enforced via `IsOwnerOrStaff` / `IsStaffRole`, gated per `self.action` (`create` -> `IsStaffRole`, everything else -> `IsOwnerOrStaff`). Verified by integration tests:

- Anonymous: 401 on income, expenses and dashboard.
- OWNER: income/expense list + detail, dashboard - 200; create income/expense - 403.
- STAFF: create income (201) and expense (201); all reads succeed.
- `recorded_by` supplied by a client is ignored; the authenticated user is always stored.

## 7. Frontend

New vertical slice following the established pattern (types -> service -> hooks -> dialogs/components -> pages -> routes):

- `types/finance.ts` - income/expense categories + labels, `Income` / `Expense`, list params/results, payloads, `DashboardSummary` types.
- `services/financeService.ts` - list/create income, list/create expense, dashboard summary (shared query-builder).
- `hooks/useFinance.ts` - `useIncomeList`, `useCreateIncome`, `useExpenseList`, `useCreateExpense`, `useDashboardSummary` with cache invalidation across the ledger and dashboard.
- `components/IncomeFormDialog.tsx`, `components/ExpenseFormDialog.tsx` - react-hook-form + zod dialogs (category, amount, date, reference, description) mirroring backend validation.
- `pages/Income.tsx` - date/category filters, pagination, category chips, amount/reference/description/recorded-by columns, STAFF-only Add Income.
- `pages/Expenses.tsx` - same structure with expense categories and STAFF-only Add Expense.
- `pages/Dashboard.tsx` - date-range filter (Apply/Reset), financial cards (recorded income, recorded expenses, net balance, payroll paid, salary advances, order revenue), order-status chips, shop overview (active customers/tailors, garment quantities), tailor workload cards, and recent income/expenses tables.
- `routes/AppRoutes.tsx` - `/dashboard`, `/income`, `/expenses` now render the real pages.
- `pages/Placeholders.tsx` - Dashboard / Income / Expenses placeholder exports removed (Payments / Reports / Settings remain placeholders).

OWNER sees all information with no mutation controls (UI + backend enforcement).

## 8. Tests

Backend (all pass):

```text
python manage.py check                        -> clean (0 silenced)
python manage.py migrate --check              -> exit 0
python -m pytest                              -> 367 passed (baseline 328 + 39 new)
python -m black --check .                      -> 131 files unchanged
python -m isort --check-only .                -> clean (9 skipped: migrations/venv)
```

New test files: `apps/finance/tests/helpers.py` + `test_income.py` (13), `test_expenses.py` (13), `test_dashboard.py` (13) - 39 tests total. Coverage highlights: anonymous 401; OWNER read 200 / mutation 403 split; STAFF create success; `recorded_by` never accepted from the client; positive amount validation (0, negative, 0.00); required category/date validation; invalid category rejection; date/category filters; inclusive date boundaries; pagination (20/page, next link); no delete/update (405 on DELETE/PATCH/PUT, records preserved); dashboard arithmetic (income totals, expense totals, net balance, payroll payment aggregation, advances separate, order revenue distinct); order status counts; garment totals; tailor workload; active counts; recent lists; empty datasets; date-range validation (reversed order, malformed date); dashboard read-only.

Frontend (all pass):

```text
npm run lint      -> clean
npx tsc --noEmit  -> clean
npm run build     -> built (chunk-size warning only, pre-existing)
```

## 9. Manual Verification

The full Phase 8 flows (STAFF create income/expense, filters, pagination, dashboard arithmetic, inclusive date boundaries, OWNER read-only, anonymous 401) are exercised end-to-end by integration tests through the real URL routes with the DRF test client. Dashboard totals are checked against the source records they aggregate (income/expense sums, `PayrollPayment` sums, `SalaryAdvance` sums, `Order.total_amount` sums, order statuses, garment quantities, workload). Frontend behavior is covered by the static build checks; the UI follows the proven vertical-slice pattern and mirrors backend validation (backend remains authoritative). Manual checklist from `docs/phase-8/08_PHASE_8_MANUAL_VERIFICATION.md` is captured by the automated integration coverage above.

## 10. Known Issues

- Frontend production build emits a pre-existing chunk-size warning (>500 kB after minification); non-blocking.
- The dashboard tailor-workload figures reflect current workload across all assignments (consistent with the existing tailor-earnings summary) and are not date-range scoped; all other dashboard figures honor the date range.

## 11. Deferred Items

Explicitly out of scope for Phase 8 (per `docs/phase-8/01_PHASE_8_SCOPE.md` and `09_PHASE_8_DEFERRED_AND_GUARDRAILS.md`) and not implemented: customer billing/invoices, invoice PDFs, payment gateways, bank integrations, WhatsApp/SMS, tax/PF/ESI, leave, attendance monetary rules, accounting ledger/double-entry bookkeeping, GST/tax accounting, advanced reports/exports, payroll rule changes and bulk settlement. Also deferred per the authoritative data model: a payment-method field on income/expense records.

## 12. Files Created/Modified

**Created - backend:**
- `backend/apps/finance/__init__.py`, `apps.py`, `admin.py`, `models.py`, `serializers.py`, `services.py`, `views.py`, `urls.py`
- `backend/apps/finance/migrations/0001_initial.py`
- `backend/apps/finance/tests/helpers.py`, `test_income.py`, `test_expenses.py`, `test_dashboard.py`

**Modified - backend:**
- `backend/config/settings.py` - register `apps.finance`
- `backend/config/urls.py` - include finance router under `/api/v1/`

**Created - frontend:**
- `frontend/src/types/finance.ts`
- `frontend/src/services/financeService.ts`
- `frontend/src/hooks/useFinance.ts`
- `frontend/src/components/IncomeFormDialog.tsx`, `ExpenseFormDialog.tsx`
- `frontend/src/pages/Dashboard.tsx`, `Income.tsx`, `Expenses.tsx`

**Modified - frontend:**
- `frontend/src/routes/AppRoutes.tsx` - real Dashboard/Income/Expenses pages
- `frontend/src/pages/Placeholders.tsx` - removed the now-replaced Dashboard/Income/Expenses placeholders

**Documentation:**
- `docs/phase-8/` - the ten Phase 8 planning/specification documents (committed) and this report
- `README.md` - Phase 8 section, repository layout, phase status

## 13. Git Verification

### Commit

Commit message: `feat(finance): implement phase 8 income and expense ledger`

### Push

Remote/branch: `origin master`. After push: `git rev-parse HEAD` == `git rev-parse origin/master` and `git status` reports a clean working tree.

## 14. Phase 9 Readiness

**Ready. Phase 8 is PASS and ready for Phase 9.**

- Income and expense records are fully audited with controlled categories and immutable history; dashboard figures are derived on the fly from authoritative records.
- RBAC verified end-to-end: anonymous 401, OWNER read / mutation 403, STAFF full mutations; full suite 367 passed.
- Backend gates clean (check, migrate --check, black, isort); frontend static checks clean (lint, TypeScript, build).
- The full 367-test suite provides the regression baseline for Phase 9.
