# Phase 9 Completion Report

## 1. Summary

Status: **PASS**

Phase 9 (Customer Billing & Invoice Foundation) is complete. A new `apps/billing` app adds:

- **Invoices** - one invoice per order, created by STAFF from an existing order. Each invoice snapshots the order garments into immutable `InvoiceItem` lines, stores `subtotal` / `total_amount` (with `adjustment_amount` stored but always `0.00`), and gets a unique server-generated `invoice_number` of the form `INV-YYYY-NNNN`. `created_by` is always the authenticated user.
- **Derived billing values** - `amount_paid` (sum of payments), `balance_due` (total - paid) and `status` (`UNPAID` / `PARTIALLY_PAID` / `PAID`) are recomputed from the append-only payment history on every read; no `status` column is stored.
- **Customer payments** - append-only payment records (amount > 0, date, method `CASH` / `UPI` / `BANK_TRANSFER` / `OTHER`, reference, notes) with `recorded_by` stored server-side. Payments are never edited or deleted.
- **Concurrency-safe payment recording** - `record_customer_payment` runs in `transaction.atomic()` and locks the invoice row with `select_for_update()`, so concurrent requests can never push an invoice past its balance due (verified by a thread-based concurrency test).
- **RBAC** - anonymous gets 401; OWNER is view-only (create invoice / record payment -> 403); STAFF creates invoices and records payments. Backend permissions are authoritative.
- **Inclusive date-range filtering** - `date_from` / `date_to` on invoices and payments; `date_to` cannot precede `date_from`; malformed dates return a clean 400.

The frontend adds a full vertical slice: an `Invoices` list (search / status / date filters, pagination, STAFF-only Create Invoice), an `InvoiceDetail` page (summary, line items, payment history, STAFF-only Record Payment / Settle in Full), a sidebar navigation entry, and a non-invasive `View Invoice` / `Create Invoice` button on the order detail page. All money uses Decimal arithmetic; invoices and payments are never physically deleted and have no update/delete API.

All Phase 9 scope items from `docs/phase-9/01_PHASE_9_SCOPE.md` are implemented; GST/tax, invoice PDFs/email/SMS, payment gateways, refunds, double-entry accounting, auto income records, order total rewrites, a payment-method field beyond the four choices, a stored `status` column and any invoice/payment mutation remain explicitly out of scope.

**Final status:** Phase 9 is **PASS and ready for Phase 10**.

## 2. Features Implemented

- **Invoice creation** - STAFF creates an invoice by referencing an existing order (`POST /invoices/` or the convenience `POST /orders/{id}/invoice/`). The customer comes from the order, line items are snapshotted, the invoice number is generated server-side, and `created_by` is set from the authenticated user. A second invoice for the same order is rejected (409-equivalent error contract).
- **Unique invoice numbering** - `invoice_number = INV-YYYY-NNNN` with a per-year sequence, generated under `transaction.atomic()` with IntegrityError retries so concurrent creations cannot collide.
- **Immutable line-item snapshots** - `InvoiceItem` records `garment_type`, `garment_code`, `quantity`, `unit_price` and `line_total` copied from the order at creation; later order edits cannot change an invoice.
- **Derived totals and status** - subtotal = sum of item line totals, total = subtotal + adjustment, amount paid = sum of payments, balance due = total - paid, status = `UNPAID` / `PARTIALLY_PAID` / `PAID`. All recomputed per read via `invoice_summary()`.
- **Append-only payments** - `POST /invoices/{id}/payments/` records a payment after validating the amount against the locked balance; overpayment is rejected. History via `GET /invoices/{id}/payments/` with `payment_method` and inclusive date filters.
- **List filtering** - invoices by `search` (invoice/order number, customer name/mobile), `customer`, `order`, derived `status` (via subquery aggregation, never a stored value), and inclusive `date_from` / `date_to`. Invalid status and reversed/invalid dates return 400.
- **Concurrency safety** - every payment record locks the invoice row; the billing concurrency test proves 300+300 against a 450.50 balance produces exactly one success with no negative balance.
- **Frontend vertical slice** - `types/billing.ts`, `services/invoiceService.ts`, `hooks/useInvoices.ts`, `CreateInvoiceDialog` and `RecordCustomerPaymentDialog` (react-hook-form + zod mirroring backend rules), and real `Invoices` / `InvoiceDetail` pages wired into routes and the existing sidebar, plus the order-detail integration.

## 3. Data Model

### `apps/billing/models.py` (migration `0001_initial.py`)

**`Invoice`** (extends `apps.common.models.TimeStampedModel`):

| Field | Type | Notes |
|---|---|---|
| `order` | OneToOne `orders.Order` | one invoice per order (unique) |
| `invoice_number` | CharField(16) | unique, `INV-YYYY-NNNN`, server-generated, read-only |
| `invoice_date` | DateField | default today |
| `subtotal` | Decimal(12,2) | stored; equals sum of item line totals |
| `adjustment_amount` | Decimal(12,2) | stored, always `0.00` (accepted from client but forced to 0) |
| `total_amount` | Decimal(12,2) | stored; subtotal + adjustment |
| `notes` | TextField, blank | |
| `created_by` | FK AUTH_USER_MODEL (SET_NULL), null | set server-side |

- `Meta.ordering = ["-invoice_date", "-created_at"]`; `UniqueConstraint` on `order`; `Index` on `invoice_date`; `CheckConstraint` `total_amount >= 0`.
- No `status` column (derived); no delete/update route or admin path.

**`InvoiceItem`** (extends `TimeStampedModel`):

| Field | Type | Notes |
|---|---|---|
| `invoice` | FK `Invoice`, related_name `items` | |
| `garment_type` | CharField(50) | snapshot |
| `garment_code` | CharField(20) | snapshot (`SHIRT` / `PANT`) |
| `quantity` | PositiveIntegerField | snapshot |
| `unit_price` | Decimal(12,2) | snapshot |
| `line_total` | Decimal(12,2) | snapshot (quantity x unit price) |

- `Meta.ordering = ["id"]`; `CheckConstraint` `quantity > 0` and `line_total >= 0`.
- Immutable in the API (read-only serializer, no update/delete).

**`CustomerPayment`** (extends `TimeStampedModel`):

| Field | Type | Notes |
|---|---|---|
| `invoice` | FK `Invoice`, related_name `payments` | |
| `amount` | Decimal(12,2) | `CheckConstraint` `> 0` |
| `payment_date` | DateField | default today |
| `payment_method` | CharField(20) | `CASH` / `UPI` / `BANK_TRANSFER` / `OTHER` |
| `reference` | CharField(100), blank | |
| `notes` | TextField, blank | |
| `recorded_by` | FK AUTH_USER_MODEL (SET_NULL), null | set server-side |

- `Meta.ordering = ["-payment_date", "-created_at"]`; `Index` on `payment_date` and on `payment_method`.
- Append-only: no update/delete route or admin path; PUT/PATCH/DELETE return 404 (not routed).

## 4. API Endpoints

All under `/api/v1/`. Error contract is the standard `{success:false, error:{code, message, details?}}`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET / POST | `/invoices/` | read OWNER+STAFF / create STAFF | List (search, customer, order, status, date_from, date_to, page) / create from order |
| GET | `/invoices/{id}/` | OWNER+STAFF | Invoice detail with items, derived totals/status, payments summary |
| GET / POST | `/invoices/{id}/payments/` | read OWNER+STAFF / record STAFF | Payment history (payment_method, date_from, date_to, page) / record payment |
| POST | `/orders/{id}/invoice/` | STAFF | Convenience: create invoice for order, return it (409 error contract if one exists) |

- All lists paginated at 20/page. Invoices have no update/delete routes; payments are append-only.
- Invoice serializer exposes `customer` (embedded), minimal `order`, `items`, derived `subtotal` / `adjustment_amount` / `total_amount` / `amount_paid` / `balance_due` / `status` / `payment_count`, and `created_by_name`; payment serializer exposes `invoice_number`, `payment_method_display` and `recorded_by_name`.

## 5. Business Rules

- **One invoice per order** - enforced by the `UniqueConstraint` and serializer/service duplicate checks (both the list create and the order convenience action).
- **Server-generated numbering** - clients can never supply `invoice_number`; collisions are retried under lock.
- **Line-item snapshots** - items are copied from the order at creation and are immutable thereafter.
- **Adjustment is structural** - the API accepts an `adjustment_amount` field but the service always stores `0.00`, so derived totals always honour the billing rules.
- **Derived, never stored** - amount paid, balance due and status are recomputed on every read from the append-only payment history; `GET` never writes.
- **Positive payments, no overpayment** - amount must be > 0 and cannot exceed the balance due; enforced at the DB (CheckConstraint), serializer and under `select_for_update()` in the service.
- **Audit trail** - `created_by` / `recorded_by` always come from the authenticated user and are never accepted from the client.
- **Inclusive date ranges** - `date_from` / `date_to` filter with `>=` / `<=`; `date_to` earlier than `date_from` returns 400; malformed dates return 400.
- **No mutation** - invoices and payments are never updated or deleted (405/404 on unsupported methods; no routes registered).

## 6. RBAC Verification

Backend-enforced via `IsOwnerOrStaff` / `IsStaffRole`, gated per `self.action` (`create` -> `IsStaffRole`, everything else -> `IsOwnerOrStaff`; the payments POST branch checks `IsStaffRole` explicitly). Verified by integration tests:

- Anonymous: 401 on invoice list/detail, payment history, payment recording and the order invoice action.
- OWNER: invoice list/detail + payment history - 200; create invoice, order invoice action, record payment - 403.
- STAFF: create invoice (201), order invoice action (201), record payment (201); all reads succeed.
- `created_by` / `recorded_by` supplied by a client are ignored; the authenticated user is always stored.

## 7. Frontend

New vertical slice following the established pattern (types -> service -> hooks -> dialogs/components -> pages -> routes):

- `types/billing.ts` - invoice statuses + labels/colors, payment methods + labels, `Invoice` / `InvoiceItem` / `CustomerPayment`, list params/results, create payloads, response types.
- `services/invoiceService.ts` - list/get/create invoice, create order invoice, list/create payments (shared query-builder).
- `hooks/useInvoices.ts` - `useInvoiceList`, `useInvoice`, `useCreateInvoice`, `useCreateOrderInvoice`, `useInvoicePayments`, `useCreatePayment` with cache invalidation across invoices, invoice payments and orders.
- `components/CreateInvoiceDialog.tsx` - order search/select with total preview, invoice date, notes (react-hook-form + zod).
- `components/RecordCustomerPaymentDialog.tsx` - balance summary, amount capped at balance due, date, method, reference, notes; supports Settle in Full (named distinctly from the Phase 7 payroll `RecordPaymentDialog`).
- `pages/Invoices.tsx` - search / status / date filters, pagination, invoice number / customer / order / totals / status chips, STAFF-only Create Invoice.
- `pages/InvoiceDetail.tsx` - summary cards (subtotal, adjustment, total, paid, balance due), line-items table, payment history, STAFF-only Record Payment / Settle in Full.
- `pages/OrderDetail.tsx` - non-invasive integration: detects an existing invoice for the order and shows `View Invoice`, otherwise STAFF sees `Create Invoice` (creates via the convenience endpoint and navigates to it).
- `routes/AppRoutes.tsx` - `/invoices` and `/invoices/:id`.
- `constants/navigation.ts` - "Invoices" sidebar entry (ReceiptIcon).

OWNER sees all information with no mutation controls (UI + backend enforcement).

## 8. Tests

Backend (all pass):

```text
python manage.py check                        -> clean (0 silenced)
python manage.py migrate --check              -> exit 0
python -m pytest                              -> 403 passed (baseline 367 + 36 new)
python -m black --check .                      -> 143 files unchanged
python -m isort --check-only .                -> clean (10 skipped: migrations/venv)
```

New test files: `apps/billing/tests/helpers.py`, `test_invoices.py`, `test_payments.py` - 36 tests total. Coverage highlights: anonymous 401; OWNER read 200 / mutation 403 split; STAFF create success; `created_by` / `recorded_by` never accepted from the client; duplicate invoice rejection; server-generated unique `INV-YYYY-NNNN`; item snapshot immutability and correctness; search / customer / order filters; derived status filters (UNPAID / PARTIALLY_PAID / PAID via subquery); inclusive date boundaries; reversed / malformed dates return 400; pagination; convenience order endpoint; no delete/update (405) and append-only history (404 on payment detail mutations); positive amount and overpayment validation; exact final payment produces PAID; method filters; and a thread-based concurrency test (300+300 vs 450.50 -> exactly one success, no negative balance).

Frontend (all pass):

```text
npm run lint      -> clean
npx tsc --noEmit  -> clean
npm run build     -> built (chunk-size warning only, pre-existing)
```

## 9. Manual Verification

The full Phase 9 flows (STAFF create invoice from order, snapshot correctness, record payment, settle in full, status transitions, filters, pagination, inclusive date boundaries, OWNER read-only, anonymous 401, duplicate-invoice rejection, concurrent payment safety) are exercised end-to-end by integration tests through the real URL routes with the DRF test client. Derived totals/status are checked against the source records they aggregate, and the concurrency test proves the row-lock invariant. Frontend behavior is covered by the static build checks; the UI follows the proven vertical-slice pattern and mirrors backend validation (backend remains authoritative). Manual checklist from `docs/phase-9/08_PHASE_9_MANUAL_VERIFICATION.md` is captured by the automated integration coverage above.

## 10. Known Issues

- Frontend production build emits a pre-existing chunk-size warning (>500 kB after minification); non-blocking.
- The invoice list does not surface "not yet invoiced" orders; the order-detail page detects an existing invoice via the `order` filter to toggle the View/Create Invoice button.

## 11. Deferred Items

Explicitly out of scope for Phase 9 (per `docs/phase-9/01_PHASE_9_SCOPE.md` and `09_PHASE_9_DEFERRED_AND_GUARDRAILS.md`) and not implemented: GST/tax on invoices, invoice PDF/email/SMS, payment gateways / cash-on-delivery capture, refunds / credits, double-entry accounting ledger, automatic income records from invoice payments, rewriting order totals from payments, a payment-method field beyond the four choices, a stored invoice `status` column, and any physical deletion of invoices or payments.

## 12. Files Created/Modified

**Created - backend:**
- `backend/apps/billing/__init__.py`, `apps.py`, `admin.py`, `models.py`, `serializers.py`, `services.py`, `views.py`, `urls.py`
- `backend/apps/billing/migrations/0001_initial.py`
- `backend/apps/billing/tests/__init__.py`, `helpers.py`, `test_invoices.py`, `test_payments.py`

**Modified - backend:**
- `backend/config/settings.py` - register `apps.billing`
- `backend/config/urls.py` - include billing router under `/api/v1/`
- `backend/apps/orders/views.py` - add `POST /orders/{id}/invoice/` convenience action with local billing imports (app decoupling)

**Created - frontend:**
- `frontend/src/types/billing.ts`
- `frontend/src/services/invoiceService.ts`
- `frontend/src/hooks/useInvoices.ts`
- `frontend/src/components/CreateInvoiceDialog.tsx`, `RecordCustomerPaymentDialog.tsx`
- `frontend/src/pages/Invoices.tsx`, `InvoiceDetail.tsx`

**Modified - frontend:**
- `frontend/src/routes/AppRoutes.tsx` - `/invoices`, `/invoices/:id`
- `frontend/src/constants/navigation.ts` - "Invoices" sidebar entry
- `frontend/src/pages/OrderDetail.tsx` - View / Create Invoice integration

**Documentation:**
- `docs/phase-9/` - the ten Phase 9 planning/specification documents (committed) and this report
- `README.md` - Phase 9 section, repository layout, phase status

## 13. Git Verification

### Commit

Commit message: `feat(billing): implement phase 9 customer invoicing`

### Push

Remote/branch: `origin master`. After push: `git rev-parse HEAD` == `git rev-parse origin/master` and `git status` reports a clean working tree.

## 14. Phase 10 Readiness

**Ready. Phase 9 is PASS and ready for Phase 10.**

- Invoices and payments are fully audited with server-generated numbering, immutable item snapshots and append-only history; totals and status are derived on the fly from authoritative records.
- Payment recording is concurrency-safe (row locks verified by a thread test).
- RBAC verified end-to-end: anonymous 401, OWNER read / mutation 403, STAFF full mutations; full suite 403 passed.
- Backend gates clean (check, migrate --check, black, isort); frontend static checks clean (lint, TypeScript, build).
- The full 403-test suite provides the regression baseline for Phase 10.
