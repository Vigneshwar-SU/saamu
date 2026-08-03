# Phase 7 Completion Report

## 1. Summary

Status: **PASS**

Phase 7 (Salary Payments, Advances & Payroll Settlement) is complete. A new `apps/payments` app adds:

- `SalaryAdvance` — salary advances given to tailors with an audit trail, statuses `OUTSTANDING` / `DEDUCTED`, and a record of which payroll entry deducted the advance.
- `PayrollPayment` — salary payments recorded against finalized payroll entries with payment method, reference, notes, and `recorded_by` audit.
- **Derived settlement** — gross payable, advance deductions, payments recorded, outstanding payable and settlement status (`UNPAID` / `PARTIALLY_PAID` / `SETTLED`) are computed on the fly and never stored, so finalized payroll calculations stay immutable.
- **Concurrency-safe mutations** — record payment, apply advance and settle-in-full all run in `transaction.atomic()` with `select_for_update()` row locks, so concurrent operations can never overpay an entry.
- **RBAC** — OWNER is read-only (settlement summaries, payment history, advances); STAFF performs all settlement mutations; anonymous gets 401.

The frontend adds an Advances page (tailor/status/date filters, pagination, STAFF-only Add Advance), settlement columns on the Payroll period list, and a per-tailor settlement panel on Payroll detail (gross/advance/paid/outstanding, payment history, STAFF-only Record Payment / Apply Advance / Settle in Full). Sidebar gains an Advances entry and a new `/advances` route.

All Phase 7 scope items from `docs/phase-7/01_PHASE_7_SCOPE.md` are implemented; tax/PF/ESI, leave, notifications, dashboard analytics, income/expense accounting, customer billing and bank/payment-gateway integrations remain explicitly out of scope.

**Final status:** Phase 7 is **PASS and ready for Phase 8**.

## 2. Features Implemented

- **Salary advances** — STAFF records an advance for any tailor (amount > 0, date, optional notes); the authenticated user is stored as `recorded_by`. Advances are never edited or deleted; a deduction is the only mutation and it moves the advance to `DEDUCTED`, linking the payroll entry and `deducted_at`.
- **Payroll payments** — STAFF records a payment against a finalized payroll entry (amount, date, method `CASH` / `BANK_TRANSFER` / `UPI` / `OTHER`, reference, notes). Amount must be positive and must not exceed the server-derived outstanding payable. Payments are never deleted or edited.
- **Partial and full settlement** — any number of partial payments can be recorded; `settle` records one final payment for the full outstanding amount. An entry reaches `SETTLED` exactly when `gross − deductions − paid <= 0`.
- **Advance deduction** — `apply-advance` deducts one `OUTSTANDING` advance of the entry's own tailor. An advance can be deducted only once, and a deduction can never make the outstanding balance negative.
- **Derived settlement everywhere** — entry serializers embed `settlement` (gross payable, advance deductions, payments recorded, outstanding payable, status, payment count); the period list/detail embed an aggregate `settlement` across all entries in the period.
- **Payment/settlement history** — per-entry payment history endpoint plus `payment_count` in every summary; nothing is physically deletable.
- **Frontend vertical slice** — Advances page, Payroll list settlement columns, Payroll detail settlement panel + payment history, and three dialogs (Add Advance, Record Payment, Settle in Full, Apply Advance) with react-hook-form + zod client validation mirroring backend rules (backend remains authoritative).

## 3. Data Model

### `apps/payments/models.py` (migration `0001_initial.py`)

**`SalaryAdvance`**:

| Field | Type | Notes |
|---|---|---|
| `tailor` | FK Tailor (PROTECT) | |
| `amount` | Decimal(12,2) | `CheckConstraint` `> 0` |
| `advance_date` | DateField | |
| `status` | CharField(20) | `OUTSTANDING` / `DEDUCTED` |
| `notes` | TextField, blank | |
| `payroll_entry` | FK PayrollEntry (PROTECT), null | set only on deduction |
| `deducted_at` | DateTimeField, null | set only on deduction |
| `recorded_by` | FK AUTH_USER_MODEL (SET_NULL), null | audited marker |

- `Meta.ordering = ["-advance_date", "-created_at"]`; `Index` on `(tailor, advance_date)` and on `status`.
- No delete/update path in the API or admin.

**`PayrollPayment`**:

| Field | Type | Notes |
|---|---|---|
| `payroll_entry` | FK PayrollEntry (PROTECT) | |
| `tailor` | FK Tailor (PROTECT) | must match the entry's tailor (enforced in services) |
| `amount` | Decimal(12,2) | `CheckConstraint` `> 0` |
| `payment_date` | DateField | |
| `payment_method` | CharField(20) | `CASH` / `BANK_TRANSFER` / `UPI` / `OTHER` |
| `reference` | CharField(100), blank | |
| `notes` | TextField, blank | |
| `recorded_by` | FK AUTH_USER_MODEL (SET_NULL), null | audited marker |

- `Meta.ordering = ["-payment_date", "-created_at"]`; `Index` on `(payroll_entry, payment_date)` and on `(tailor, payment_date)`.
- No delete/update path.

## 4. API Endpoints

All under `/api/v1/`. Error contract is the standard `{success:false, error:{code, message, details?}}`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET / POST | `/advances/` | read OWNER+STAFF / create STAFF | List (tailor, status, date_from, date_to, page) / create |
| GET | `/advances/{id}/` | OWNER+STAFF | Advance detail |
| GET | `/payroll/entries/{id}/settlement/` | OWNER+STAFF | Per-entry settlement summary |
| GET / POST | `/payroll/entries/{id}/payments/` | read OWNER+STAFF / create STAFF | Payment history / record a payment |
| POST | `/payroll/entries/{id}/apply-advance/` | STAFF | Deduct an OUTSTANDING advance (body `advance_id`) |
| POST | `/payroll/entries/{id}/settle/` | STAFF | Record one final payment for the full outstanding amount |

- Payroll period list/detail and entry list embed `settlement` (entry-level and period-aggregate).
- All lists paginated at 20/page.

## 5. Business Rules

- **FINALIZED only** — payment, advance deduction and settle mutations reject any payroll period that is not `FINALIZED` (`{"detail": "Only finalized payroll periods can be settled."}`).
- **Derived, never stored** — `outstanding = gross_payable − advance_deductions − payments_recorded`; `gross_payable` is the immutable Phase 6 `total_payable`. Finalized payroll calculations are never rewritten.
- **Overpayment prevention** — payment amount must be `> 0` and `<= outstanding_payable`; an advance must be `<= outstanding_payable` (a deduction can never make the balance negative).
- **Advance deducted once** — an advance that is already `DEDUCTED` cannot be applied again.
- **Tailor match** — the advance's tailor must equal the payroll entry's tailor; payments always inherit the entry's tailor server-side.
- **Audit trail** — every advance and payment records `recorded_by`; history is never physically deleted.
- **Concurrency** — all settlement mutations lock the payroll entry (and the advance for deductions) with `select_for_update()` inside `transaction.atomic()`, so concurrent operations cannot overpay.

## 6. RBAC Verification

Backend-enforced via `IsOwnerOrStaff` / `IsStaffRole`, gated per `self.action` (`SETTLEMENT_MUTATION_ACTIONS = {"payments", "settle", "apply_advance"}`, plus advances create). Verified by integration tests:

- Anonymous: 401 on advances and all settlement endpoints.
- OWNER: advance list/detail, settlement summary, payment history → 200; create advance, record payment, apply advance, settle → 403.
- STAFF: create advance (201), record payment (201/200), apply advance (200), settle (200); all reads succeed.

## 7. Frontend

New vertical slice following the established pattern (types → service → hooks → dialogs/components → pages → routes):

- `types/advances.ts` — advance statuses/labels/colors, `SalaryAdvance`, list params/result, payload.
- `types/payroll.ts` — settlement status/method constants, `PayrollSettlement`, `PayrollPayment`, payload/response types; `PayrollPeriod` and `PayrollEntry` now carry `settlement`.
- `services/advanceService.ts` — list (query params)/get/create.
- `services/payrollService.ts` — getSettlement/listPayments/recordPayment/settleEntry/applyAdvance.
- `hooks/useAdvances.ts` — advance list/create with cache invalidation.
- `hooks/usePayroll.ts` — settlement, payment history, record payment, settle, apply-advance hooks with query invalidation.
- `components/AddAdvanceDialog.tsx`, `components/RecordPaymentDialog.tsx` (supports settle-in-full mode with amount locked to outstanding), `components/ApplyAdvanceDialog.tsx` — react-hook-form + zod dialogs; the payment dialog shows gross/advance/paid/current outstanding/maximum payable.
- `pages/Advances.tsx` — tailor/status/date filters, pagination, status chips, recorded-by column, STAFF-only Add Advance.
- `pages/Payroll.tsx` — added Paid / Outstanding / Settlement status columns per period.
- `pages/PayrollDetail.tsx` — 12-column tailor table (now incl. Advance/Paid/Outstanding/Settlement), per-tailor assignment breakdown, and a settlement panel with summary cards, payment history and STAFF-only Record Payment / Apply Advance / Settle in Full.
- `constants/navigation.ts` — Advances sidebar item; `routes/AppRoutes.tsx` — `/advances`.

OWNER sees all settlement information but no mutation controls (UI + backend enforcement).

## 8. Tests

Backend (all pass):

```text
python manage.py check                        → clean (0 silenced)
python manage.py migrate --check              → exit 0
python -m pytest                              → 328 passed (baseline 291 → 328)
python -m black --check .                      → 118 files unchanged
python -m isort --check-only .                → clean (8 skipped: migrations/venv)
```

New test files: `apps/payments/tests/helpers.py` + `test_advances.py` (8), `test_payments.py` (12), `test_settlement.py` (17) — 37 tests total. Coverage highlights: anonymous 401; OWNER read 200 / mutation 403 split; STAFF create/record/apply/settle; positive amounts required; overpayment rejected; payment tailor must match entry tailor; FINALIZED-only enforcement; multiple partial payments; exact final payment → `SETTLED`; exact-decimal arithmetic (5 × 150.25 = 751.25, 300.15 payment → 451.10 outstanding); advance applied once, no double deduction, wrong-tailor and exceeds-outstanding rejections; archived-tailor advance history visible; no delete/update (405 on unsupported methods); history preserved; period list embeds period-level settlement aggregate; and a `transaction=True` concurrency test where two threads race to record 500 each against a 750 entry and exactly one succeeds (no overpayment).

Frontend (all pass):

```text
npm run lint      → clean
npx tsc --noEmit  → clean
npm run build     → built (chunk-size warning only, pre-existing)
```

## 9. Manual Verification

The full settlement flows (finalize → record partial payments → apply advance → settle in full, overpayment/duplicate-deduction/wrong-tailor rejections, RBAC, and concurrent overpayment protection) are exercised end-to-end by integration tests through the real URL routes with the DRF test client. The period-level settlement aggregate is verified against the period list endpoint. Frontend behavior is covered by the static build checks; the UI follows the proven Phase 3–6 vertical-slice patterns and mirrors backend validation (backend remains authoritative).

## 10. Known Issues

- Frontend production build emits a pre-existing chunk-size warning (>500 kB after minification); non-blocking.
- `attendance_amount` is still always `0` because no monetary attendance rule is configured (inherited from Phase 6); gross payable therefore equals piece-rate earnings until that rule exists.

## 11. Deferred Items

Explicitly out of scope for Phase 7 (per `docs/phase-7/01_PHASE_7_SCOPE.md`) and not implemented: tax/PF/ESI deductions, leave management, notifications/WhatsApp/SMS, dashboard analytics, income/expense accounting, customer billing/invoices, and bank/payment-gateway integrations. Also deferred: period-level bulk settle-all, payment scheduling, advance limits/caps, and any change to finalized payroll calculations (immutability guardrail).

## 12. Files Created/Modified

**Created — backend:**
- `backend/apps/payments/__init__.py`, `apps.py`, `admin.py`, `models.py`, `serializers.py`, `services.py`, `views.py`, `urls.py`
- `backend/apps/payments/migrations/0001_initial.py`
- `backend/apps/payments/tests/helpers.py`, `test_advances.py`, `test_payments.py`, `test_settlement.py`

**Modified — backend:**
- `backend/config/settings.py` — register `apps.payments`
- `backend/config/urls.py` — include payments router under `/api/v1/`
- `backend/apps/payroll/serializers.py` — embed `settlement` on period and entry output
- `backend/apps/payroll/views.py` — settlement/payments/settle/apply-advance actions + RBAC gating

**Created — frontend:**
- `frontend/src/types/advances.ts`
- `frontend/src/services/advanceService.ts`
- `frontend/src/hooks/useAdvances.ts`
- `frontend/src/components/AddAdvanceDialog.tsx`, `RecordPaymentDialog.tsx`, `ApplyAdvanceDialog.tsx`
- `frontend/src/pages/Advances.tsx`

**Modified — frontend:**
- `frontend/src/types/payroll.ts` — settlement/payment types + `settlement` on period/entry
- `frontend/src/services/payrollService.ts` — settlement/payment/advance mutations
- `frontend/src/hooks/usePayroll.ts` — settlement/payment/advance hooks
- `frontend/src/pages/Payroll.tsx` — settlement columns
- `frontend/src/pages/PayrollDetail.tsx` — settlement panel, payment history, dialogs
- `frontend/src/constants/navigation.ts` — Advances sidebar item
- `frontend/src/routes/AppRoutes.tsx` — `/advances`

**Documentation:**
- `docs/phase-7/` — the ten Phase 7 planning/specification documents (committed) and this report
- `README.md` — Phase 7 section, repository layout, phase status

## 13. Git Verification

### Commit

Commit message: `feat(payments): implement phase 7 payroll settlement`

### Push

Remote/branch: `origin master`. After push: `git rev-parse HEAD` == `git rev-parse origin/master` and `git status` reports a clean working tree.

## 14. Phase 8 Readiness

**Ready. Phase 7 is PASS and ready for Phase 8.**

- Advances and payments are fully audited; finalized payroll remains immutable and settlement is always derived.
- All settlement mutations are concurrency-safe and overpayment-proof, verified by a threaded integration test.
- RBAC verified end-to-end: anonymous 401, OWNER read / mutation 403, STAFF full mutations; full suite 328 passed.
- Frontend static checks clean; the Advances/payroll-settlement UI follows the proven vertical-slice pattern.
- The full 328-test suite provides the regression baseline for Phase 8.
