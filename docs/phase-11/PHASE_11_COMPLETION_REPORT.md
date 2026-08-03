# Phase 11 Completion Report

## 1. Status

**PASS** (with manual verification recorded separately — see section 10).

Phase 11 (Payments & Billing) is complete. It extends the Phase 9 invoice foundation into the full customer payment and digital-billing layer: explicit `ADVANCE` / `PARTIAL` / `FINAL` / `REFUND` payment types, refunds recorded as auditable transactions (never mutations of history), backend-authoritative order total / total paid / outstanding balance / payment status, and a digital bill rendered entirely from database data.

All Phase 11 scope items from `docs/phase-11/01_PHASE_11_SCOPE.md` are implemented. PDF/WhatsApp/SMS, payment gateways, GST, double-entry accounting and automatic income records remain explicitly out of scope. Phase 7 settlement logic (`apps/payments`) and finalized payroll are untouched.

## 2. Scope

In scope and delivered:

- Customer payments with explicit types: **ADVANCE**, **PARTIAL**, **FINAL**, **REFUND**.
- **Order total** — the order's authoritative `total_amount` (from line items).
- **Total paid** — net of refunds, derived server-side from append-only payment rows.
- **Outstanding balance** — order total minus net paid, derived server-side.
- **Payment status** — `UNPAID` / `PARTIALLY_PAID` / `PAID`, always derived, never stored.
- **Digital bill** containing shop, customer, order, garment, payment and date details.
- Integration with the existing order/customer foundations; Phase 7 settlement and finalized payroll preserved.

Out of scope (deferred, not implemented): PDF salary slips, WhatsApp/SMS, payment gateways, GST/accounting automation, double-entry accounting, automatic income records, any change to finalized payroll.

## 3. Implementation Summary

- `CustomerPayment` gained a `payment_type` (default `PARTIAL`) and an optional self-referencing `refunded_payment` (audit link from a REFUND back to the transaction it reverses). Payments remain append-only — no update/delete path exists.
- `record_customer_payment` (in `apps.billing.services`) now validates payment types against the server-derived balance **under the invoice row lock** (`select_for_update()` + `transaction.atomic()`), so concurrent requests can never overpay, clear with an invalid FINAL, or refund more than the customer has paid:
  - `ADVANCE` — must not exceed the outstanding balance.
  - `PARTIAL` — must be strictly less than the balance (an amount that clears the balance is FINAL).
  - `FINAL` — must equal the outstanding balance exactly.
  - `REFUND` — must not exceed the total paid (net of earlier refunds); may reference the original payment; may not reference another refund.
  - Omitted `payment_type` is derived from the amount (FINAL when it clears the balance, else PARTIAL), preserving Phase 9 behavior.
- `invoice_summary` became refund-aware: `amount_paid = gross_paid − refunded_amount` where gross = sum of non-REFUND payments and refunded = sum of REFUND payments; `balance_due = total − amount_paid`; status derived from those values. The invoice `status` list filter was updated to use the same net-of-refund arithmetic.
- A new `ShopDetails` singleton model (default name "Saamu Tailors", established year 1954, plus editable tagline/address/phone) supplies the shop block on the bill; `shop_details()` creates the row with defaults on first access.
- New `GET /api/v1/invoices/{id}/bill/` endpoint assembles the full digital bill (shop, bill metadata, customer, order, garment snapshots, payment history, totals) — no mock or client-supplied data.
- The order detail endpoint now includes an authoritative `payment_summary` (`order_total`, `total_paid`, `outstanding_balance`, `payment_status`, `payment_count`, `refunded_amount`, `has_invoice`), so the order page can show billing state before navigating to the invoice.
- Frontend: typed payment types on the record-payment dialog (with FINAL/partial/refund-aware validation), a Record Refund flow, a payment-type column and net/gross/refunded summary cards on the invoice detail, a print-friendly digital bill page at `/invoices/:id/bill`, and an order-detail Billing card showing order total / total paid / outstanding balance / payment status.

## 4. Backend Changes

- `apps/billing/models.py`
  - `ShopDetails(TimeStampedModel)` — singleton shop profile: `name` (default "Saamu Tailors"), `tagline`, `address`, `phone`, `established_year` (default 1954); `shop_details()` classmethod returns/creates the single row.
  - `CustomerPayment` — added `PaymentType` TextChoices (`ADVANCE`/`PARTIAL`/`FINAL`/`REFUND`, default `PARTIAL`), `payment_type` CharField, `refunded_payment` self-FK (`SET_NULL`, `related_name="refunds"`), new `payment_type` index; existing `amount > 0` check constraint retained.
- `apps/billing/services.py`
  - `invoice_summary` — now returns `gross_paid`, `refunded_amount`, net `amount_paid`, `balance_due`, derived `status` and `payment_count`.
  - `order_payment_summary(order)` — authoritative order-level `order_total`, `total_paid`, `outstanding_balance`, `payment_status`, `payment_count`, `refunded_amount`, `has_invoice`.
  - `shop_details_data()` and `build_bill_data(invoice)` — bill assembler.
  - `record_customer_payment` — type validation under the row lock; refund rules; explicit-type acceptance; derived type when omitted.
- `apps/billing/serializers.py` — `CustomerPaymentSerializer` exposes `payment_type`, `payment_type_display`, `refunded_payment`; `CustomerPaymentCreateSerializer` accepts optional `payment_type` and `refunded_payment` (validated against the URL invoice); `InvoiceSerializer` exposes `gross_paid` and `refunded_amount`.
- `apps/billing/views.py` — `payments` POST forwards type/refund fields; new `bill` detail action; refund-aware `status` list filter (net-of-refund `Case`/`Coalesce` annotation).
- `apps/billing/admin.py` — `ShopDetailsAdmin` (singleton-guarded add), `CustomerPaymentAdmin` shows/filters `payment_type`.
- `apps/orders/serializers.py` — `OrderSerializer` gains `payment_summary` (populated on detail via serializer context, `null` on list) using `apps.billing.services.order_payment_summary`.
- `apps/orders/views.py` — `get_serializer_context` sets `include_payment_summary` for the `retrieve` action.

## 5. Frontend Changes

- `types/billing.ts` — `PAYMENT_TYPES`, `PaymentType`, `PAYMENT_TYPE_LABELS`; `Invoice` gains `gross_paid` / `refunded_amount`; `CustomerPayment` gains `payment_type`, `payment_type_display`, `refunded_payment`; `CustomerPaymentPayload` gains `payment_type` / `refunded_payment`; new `Bill*` types and `BillResponse`.
- `services/invoiceService.ts` — `getBill(invoiceId)`.
- `hooks/useInvoices.ts` — `useInvoiceBill` (query key `'invoice-bill'`), and `useCreatePayment` invalidates the bill cache after a payment/refund.
- `components/RecordCustomerPaymentDialog.tsx` — payment-type select (ADVANCE/PARTIAL/FINAL/REFUND), refund mode with original-payment selector (refundable payments only) and refund-aware amount validation; FINAL/partial/advance amount rules mirror the backend.
- `pages/InvoiceDetail.tsx` — payment-type chips in history, net/gross/refunded summary cards, Record Refund button (STAFF, when net paid > 0), View Bill button.
- `pages/InvoiceBill.tsx` — new print-friendly digital bill (shop block, billed-to, order, garments, totals, payment history, status, generated timestamp, `window.print()`).
- `pages/OrderDetail.tsx` — Billing card showing order total / total paid / outstanding balance / payment status (from `order.payment_summary`) with a View Invoice shortcut.
- `types/orders.ts` — `Order` gains `payment_summary` (typed via `OrderPaymentSummary` in `types/billing.ts`).
- `routes/AppRoutes.tsx` — `/invoices/:id/bill`.

## 6. Database Changes

Migration `backend/apps/billing/migrations/0002_shopdetails_customerpayment_payment_type_and_more.py`:

- Create `ShopDetails` model.
- Add `customerpayment.payment_type` (CharField(12), choices, default `PARTIAL`).
- Add `customerpayment.refunded_payment` (self-FK, `SET_NULL`, related_name `refunds`).
- Add index on `customerpayment.payment_type`.

No stored `status` column was added; payment status remains derived (guardrail honored).

## 7. API Changes

All under `/api/v1/`, standard error contract `{success:false, error:{code, message, details?}}`, `COERCE_DECIMAL_TO_STRING=False` (Decimals serialize as numbers).

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET / POST | `/invoices/{id}/payments/` | read OWNER+STAFF / POST STAFF | Payment history / record a typed payment (`payment_type`, optional `refunded_payment`) |
| GET | `/invoices/{id}/bill/` | OWNER+STAFF | Digital bill (shop, customer, order, garments, payments, totals, date) |
| GET | `/invoices/{id}/` | OWNER+STAFF | Invoice detail now includes `gross_paid`, `refunded_amount` |
| GET | `/invoices/` | OWNER+STAFF | List `status` filter now uses net-of-refund paid amounts |
| GET | `/orders/{id}/` | OWNER+STAFF | Order detail now includes `payment_summary` (order total, paid, outstanding, status) |

Invoice create and order-invoice endpoints are unchanged from Phase 9. No update/delete routes exist for invoices or payments.

## 8. RBAC

Backend-enforced and unchanged in shape from Phase 9:

- Anonymous → 401 for every billing/payment/bill endpoint.
- OWNER → read access (invoice list/detail, payment history, bill); all mutations (create invoice, record payment, record refund) rejected with 403.
- STAFF → full access including all payment/refund mutations.
- `recorded_by` is always the authenticated user, never client-supplied (regression-tested).
- Frontend hides mutation controls for OWNER and shows them for STAFF only; the backend remains authoritative.

## 9. Testing Results

Backend (all pass):

```text
python manage.py check                              -> System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run    -> No changes detected
python -m pytest apps/billing                        -> 66 passed (Phase 9 + Phase 11)
python -m pytest (full suite)                        -> 455 passed (baseline 425 + 30 new)
python -m black --check apps                         -> clean
python -m isort --check-only apps                    -> clean (skipped 9: migrations/venv)
```

New test files (30 tests):

- `apps/billing/tests/test_payment_types.py` (19) — explicit ADVANCE/PARTIAL/FINAL/REFUND rules, derived type when omitted, PARTIAL-must-be-less, FINAL-must-equal, refund ≤ total paid, refund link auditability (original untouched, `refunds` back-reference), refund-belonging-to-invoice validation, cannot refund a refund, refund reduces net paid and re-derives status (PAID → PARTIALLY_PAID → UNPAID at full refund), status list filter uses net paid, refund-then-refill returns to PAID.
- `apps/billing/tests/test_bill.py` (11) — anonymous denied, OWNER read, `ShopDetails` singleton creation/defaults/editing reflected on the bill, bill customer/order/garments/metadata/totals correctness, payment history on the bill, no-mock-data guard, plus `order_payment_summary` (no invoice, typed-payment net totals) and the order-detail `payment_summary` endpoint integration.

Frontend (all pass):

```text
npm run lint      -> clean (eslint flat config, max-warnings 0)
npx tsc --noEmit  -> clean
npm run build     -> built (chunk-size warning only, pre-existing)
```

Phase 7 settlement and payroll regression tests remain green in the full suite; billing code never touches `apps/payments` or finalized payroll.

## 10. Manual Verification Status

**NOT STARTED.**

Per `docs/phase-11/08_PHASE_11_MANUAL_VERIFICATION.md`, automated tests do not count as manual verification. The Phase 11 flows (advance/partial/final/refund recording through the UI, totals/status updates, bill contents, RBAC split, and order/payroll regression) are exercised end-to-end by integration tests through the real URL routes with the DRF test client, and frontend behavior is covered by the static build checks — but the manual checklist has **not** been run against a running application and must not be claimed as done. The checklist status will be updated when a human has actually exercised the flows.

## 11. Documentation

- `docs/phase-11/` — the ten Phase 11 planning/specification documents (committed before implementation) and this completion report.
- `README.md` — current stage updated to Phase 11, repository layout `billing/` description updated, phase status list updated (`Phase 11 — Payments & Billing: complete`).

## 12. Files Changed

**Created — backend:**
- `backend/apps/billing/migrations/0002_shopdetails_customerpayment_payment_type_and_more.py`
- `backend/apps/billing/tests/test_payment_types.py`
- `backend/apps/billing/tests/test_bill.py`

**Modified — backend:**
- `backend/apps/billing/models.py` — `ShopDetails`, `CustomerPayment.payment_type` / `refunded_payment` (+ docstring)
- `backend/apps/billing/services.py` — refund-aware `invoice_summary`, `order_payment_summary`, `shop_details_data`, `build_bill_data`, typed `record_customer_payment`
- `backend/apps/billing/serializers.py` — payment type/refund fields, invoice gross/refunded fields
- `backend/apps/billing/views.py` — bill action, refund-aware status filter, POST forwarding of type fields
- `backend/apps/billing/admin.py` — `ShopDetailsAdmin`, `CustomerPaymentAdmin` payment_type column/filter
- `backend/apps/billing/tests/helpers.py` — `invoice_bill_url`
- `backend/apps/orders/serializers.py` — `payment_summary` on order detail
- `backend/apps/orders/views.py` — `include_payment_summary` serializer context for detail

**Created — frontend:**
- `frontend/src/pages/InvoiceBill.tsx`

**Modified — frontend:**
- `frontend/src/types/billing.ts` — payment types, invoice gross/refunded, bill types, `OrderPaymentSummary`
- `frontend/src/types/orders.ts` — `Order.payment_summary`
- `frontend/src/services/invoiceService.ts` — `getBill`
- `frontend/src/hooks/useInvoices.ts` — `useInvoiceBill`, bill cache invalidation
- `frontend/src/components/RecordCustomerPaymentDialog.tsx` — type select + refund mode
- `frontend/src/pages/InvoiceDetail.tsx` — type chips, summary cards, refund + bill buttons
- `frontend/src/pages/OrderDetail.tsx` — Billing card (order total / paid / outstanding / status)
- `frontend/src/routes/AppRoutes.tsx` — `/invoices/:id/bill`

**Documentation:**
- `docs/phase-11/PHASE_11_COMPLETION_REPORT.md`
- `README.md`

## 13. Known Issues

- Frontend production build emits a pre-existing chunk-size warning (>500 kB after minification); non-blocking and pre-dates Phase 11.
- `DRF COERCE_DECIMAL_TO_STRING=False` means API JSON returns Decimals as numbers (e.g. `350.5`); DB/Django values remain `Decimal` and tests assert accordingly.
- The `refunded_payment` reference is optional (a refund may be recorded without linking to an original payment); audit completeness is best-effort by design so STAFF is not forced to pick a payment.
- The sidebar "Payments" entry (`/payments`) remains the pre-existing placeholder page; customer payment workflows live under Invoices. No new page was added because the frontend spec only requires the payment and bill workflows, which are delivered.

## 14. Deferred Items

Explicitly out of scope for Phase 11 (per `docs/phase-11/01_PHASE_11_SCOPE.md` and `09_PHASE_11_DEFERRED_AND_GUARDRAILS.md`) and not implemented: PDF salary slips, WhatsApp/SMS delivery, payment gateways, GST/accounting automation, double-entry accounting, automatic income records from customer payments, and any change to finalized payroll. Phase 7 settlement logic remains authoritative and untouched.

## 15. Git Verification

### Commit

Commit message: `feat(billing): implement phase 11 payments and billing`

### Push

Remote/branch: `origin master`. After push: `git rev-parse HEAD` == `git rev-parse origin/master` and `git status` reports a clean working tree.

## 16. Phase 12 Readiness

**Ready. Phase 11 is PASS and ready for Phase 12.**

- Payment types are validated server-side under the invoice row lock (no overpayment, no invalid FINAL, no over-refund, refunds can't reference refunds); totals and status are always derived, never stored.
- Refunds are explicit append-only transactions linked back to the original payment, so financial history is auditable and never silently rewritten.
- The digital bill is assembled from database data (ShopDetails singleton, customer, order, garment snapshots, payment history) — no mock data.
- RBAC verified end-to-end (anonymous 401, OWNER read-only, STAFF mutations); full suite `455 passed`; backend and frontend gates clean.
- The full 455-test suite provides the regression baseline for Phase 12.
