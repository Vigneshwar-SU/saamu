# Phase 4 Completion Report

## 1. Summary

Phase 4 (Orders & Tailoring Workflow) is complete. The Orders placeholder is replaced by a real, role-aware order management module: a Django `apps/orders` app backed by a validated REST API with a controlled status lifecycle, immutable measurement snapshots on each order item, and a full frontend (list + detail + create dialog). All Phase 4 scope items from `docs/phase-4/01_PHASE_4_SCOPE.md` are implemented; Phase 5+ items (payments, billing, tailors workload, dashboard, notifications) are explicitly deferred.

Implemented:

- **Order model + API** — `Order` (human-friendly unique `ORD-YYYY-NNNN`), `OrderItem` (garment, quantity, unit price, measurement reference + version + snapshot), `OrderStatusHistory` (append-only audit trail). List (search by order number/customer name/mobile, status filter, date range, 20/page pagination), detail, STAFF create, STAFF safe PATCH (notes / expected delivery date only). No physical delete.
- **Status lifecycle** — `NEW → CUTTING → STITCHING → READY → COLLECTED` with `CANCELLED` allowed from any non-terminal state; `COLLECTED`/`CANCELLED` terminal; transitions only via `POST /api/v1/orders/{id}/status/`; `collected_at` set on collection; every transition (including the initial NEW row) appended to `OrderStatusHistory`.
- **Measurement snapshot strategy** — each item stores a direct reference to the exact `Measurement` row/version plus an immutable JSON snapshot of the garment's allowed fields captured at order time; later updates to the customer's measurement chart never alter historical orders.
- **RBAC** — backend-authoritative: OWNER = view-only (list/detail), STAFF = all mutations; anonymous = 401. Verified by integration tests.
- **Frontend** — real Orders list (search / status filter / pagination, STAFF-only New Order), Order detail (summary, items with expandable measurement snapshot, status history timeline, STAFF Edit + Move-to-next-status + Cancel), and a Create Order dialog (customer autocomplete, dynamic items, per-garment measurement selection with completeness validation).
- **Tests** — full backend suite at **183 passed** (140 Phase 1–3 tests remain green); frontend lint / tsc / build all clean.

**Final status:** Phase 4 is **PASS and ready for Phase 5**.

## 2. Implemented Features

- Order creation for an existing active customer with one or more garment items (SHIRT / PANT), each with quantity, per-piece unit price, and a validated measurement selection.
- Order listing with search, status filter, and order-date range filters, plus pagination.
- Order detail with nested customer, items (with measurement snapshot + version), and full status history.
- Controlled status transitions with backend-enforced lifecycle rules and a complete audit trail.
- Safe partial edits (notes, expected delivery date) — customer, items, dates, amounts, and status are immutable through PATCH.
- No physical deletion: DELETE is not exposed; orders can only reach a terminal state (COLLECTED / CANCELLED).
- Measurement data is preserved per order item via reference + snapshot (see §6).

## 3. Data Model

All in `apps/orders/models.py` (migration `apps/orders/migrations/0001_initial.py`).

**`OrderStatus`** (TextChoices): `NEW`, `CUTTING`, `STITCHING`, `READY`, `COLLECTED`, `CANCELLED`. `ALLOWED_TRANSITIONS` and `TERMINAL_STATUSES` define the lifecycle (§5).

**`Order`**:

| Field | Type | Notes |
|---|---|---|
| `order_number` | CharField(20), unique | `ORD-YYYY-NNNN`, zero-padded, generated on save |
| `customer` | FK Customer | `related_name="orders"`, cascade |
| `order_date` | DateField | default today |
| `expected_delivery_date` | DateField, null | optional; validated ≥ order_date |
| `status` | CharField(12) | default `NEW` |
| `notes` | TextField(4000), blank | |
| `total_amount` | DecimalField(10,2) | sum of line totals, computed on create, never float |
| `collected_at` | DateTimeField, null | set when status becomes COLLECTED |
| `created_at` / `updated_at` | DateTimeField | auto-set |

- Indexes: `order_date`, `status`, `(customer, order_date)`; `Meta.ordering = ["-id"]`.

**`OrderItem`**:

| Field | Type | Notes |
|---|---|---|
| `order` | FK Order | `related_name="items"`, cascade |
| `garment_type` | CharField(10) | SHIRT / PANT |
| `quantity` | PositiveIntegerField | ≥ 1 |
| `measurement` | FK Measurement, null | exact row/version used |
| `measurement_version` | PositiveInteger, null | version captured at order time |
| `measurement_snapshot` | JSONField, null | immutable values at order time (§6) |
| `unit_price` | DecimalField(10,2) | per piece, INR |
| `notes` | TextField(2000), blank | |
| `created_at` / `updated_at` | DateTimeField | auto-set |

- `amount` property computes `unit_price * quantity`; never stored.
- Index on `(order, garment_type)`; `Meta.ordering = ["id"]`.

**`OrderStatusHistory`**:

| Field | Type | Notes |
|---|---|---|
| `order` | FK Order | `related_name="status_history"`, cascade |
| `from_status` | CharField(12), null | None for the initial NEW row |
| `to_status` | CharField(12) | |
| `changed_by` | FK User, null | staff who performed the change |
| `changed_at` | DateTimeField | default now |

- Append-only; entries never mutated or deleted. Index on `(order, changed_at)`; `Meta.ordering = ["changed_at", "id"]`.

## 4. API Endpoints

All under `/api/v1/`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/v1/orders/` | OWNER + STAFF | List; `?search=&status=&date_from=&date_to=&page=` |
| GET | `/api/v1/orders/{id}/` | OWNER + STAFF | Detail with items + status history |
| POST | `/api/v1/orders/` | STAFF | Create (customer + items) |
| PATCH | `/api/v1/orders/{id}/` | STAFF | Safe update: notes, expected_delivery_date only |
| POST | `/api/v1/orders/{id}/status/` | STAFF | Status transition: `{"status": "CUTTING"}` |
| DELETE | — | — | Not exposed (`http_method_names` excludes it → 405) |

- **Search** is case-insensitive on `order_number`, `customer.full_name`, `customer.mobile_number`.
- **Status filter** validates against `OrderStatus.values` (invalid → 400 `validation_error`).
- **Date range** filters by `order_date` inclusive (YYYY-MM-DD).
- **Create validation**: customer must exist and be active; ≥1 item; quantity ≥ 1; unit price ≥ 0; expected delivery ≥ order date; every item must reference an existing measurement belonging to that customer and garment, which must be complete for that garment (all `GARMENT_REQUIRED_FIELDS` present).
- **Transition validation**: only forward transitions in `ALLOWED_TRANSITIONS`; terminal orders cannot change; invalid/unknown statuses → 400 `validation_error`.
- Standardized error shape `{success:false, error:{code, message}}` throughout; `Http404` → `not_found` (Phase 3 fix).

## 5. Order Lifecycle

```
NEW ──► CUTTING ──► STITCHING ──► READY ──► COLLECTED   (terminal)
 └─────────────► CANCELLED (allowed from NEW, CUTTING,
                 STITCHING, READY)                       (terminal)
```

- Every transition must come through `POST /orders/{id}/status/`; PATCHing `status` is silently ignored (field is not in the update serializer).
- The initial `NEW` state is recorded as a history row (`from_status=None`) at creation.
- `COLLECTED` sets `collected_at`; `CANCELLED` never sets it.
- `COLLECTED` and `CANCELLED` are terminal — no further transitions.

## 6. Measurement Snapshot Strategy

Two-layer preservation on each `OrderItem`:

1. **Direct reference** — `measurement` FK points at the exact `Measurement` row/version used at order time (Phase 3 history rows are immutable, so the reference is stable in practice).
2. **Immutable snapshot** — `measurement_snapshot` JSON stores only the garment's `GARMENT_ALLOWED_FIELDS` values as plain numbers, captured in the create serializer and written via `bulk_create`. The snapshot is self-contained and survives any later change to the customer's measurement chart (verified by `test_order_measurement_snapshot.py`).

The API always serves the snapshot + version for historical accuracy; the live measurement row is never mutated or read through for order display.

## 7. RBAC Verification

Backend-authoritative (integration tests in `apps/orders/tests/`):

| Action | OWNER | STAFF | Anonymous |
|---|---|---|---|
| GET list | 200 | 200 | 401 |
| GET detail | 200 | 200 | 401 |
| POST create | 403 | 201 | 401 |
| PATCH safe update | 403 | 200 | 401 |
| POST status transition | 403 | 200 | 401 |
| DELETE | 405 | 405 | 401 |

Role gates reuse the Phase 2 `IsOwnerOrStaff` / `IsStaffRole` permission classes; the status action is registered under its DRF action name `change_status` so the STAFF-only gate applies.

## 8. Frontend

- `src/types/orders.ts` — `OrderStatus`, `Order`, `OrderItem`, `OrderStatusHistoryEntry`, list/create/update/status payloads, status labels/colors.
- `src/services/orderService.ts` — list/get/create/update/changeStatus via `apiClient`.
- `src/hooks/useOrders.ts` — `useOrderList`, `useOrder`, `useCreateOrder`, `useUpdateOrder`, `useChangeOrderStatus` on TanStack Query with invalidation.
- `src/pages/Orders.tsx` — real list replacing the placeholder: debounced search, status filter, 20/page pagination, loading/empty/error+retry states, per-status colored chips, STAFF-only New Order, row click → detail.
- `src/pages/OrderDetail.tsx` — order summary cards, items table with per-item "View measurements used" expandable snapshot, total row, status history timeline (from/to, staff member, timestamp), STAFF Edit dialog (notes + expected delivery), "Move to next status" and "Cancel" actions with confirm; terminal/OWNER states hide mutation controls.
- `src/components/CreateOrderDialog.tsx` — customer autocomplete (debounced search), dynamic garment items (garment / quantity / unit price / measurement version select), measurement completeness + version display, incomplete measurements disabled, client-side validation mirroring backend rules, server errors surfaced via `getApiErrorMessage`.
- Routes: `/orders` and `/orders/:id` added in `AppRoutes.tsx`; Orders placeholder removed from `Placeholders.tsx`.
- OWNER sees view-only UI (no create/edit/transition/cancel controls).

## 9. Tests

### Backend

**183 passed** (`python -m pytest`, ~77s) — all 140 Phase 1–3 tests remain green. New `apps/orders/tests/`:

- `test_order_crud.py` — create (single/multi-garment, totals, order-number sequence uniqueness), retrieve, list pagination (25 records → 20 + next), search by number and customer name, status filter (valid/invalid), date filters, quantity/price/date validation, requires ≥1 item, archived customer rejected, safe-PATCH only (notes/delivery), PATCH cannot change status, no DELETE (405, row retained).
- `test_order_measurement_validation.py` — measurement required per item, missing/wrong-customer/wrong-garment/incomplete measurements rejected, historical (non-current) version selectable.
- `test_order_status.py` — initial NEW history row, full valid chain `NEW→…→COLLECTED` with `collected_at`, history records every transition, skipped/backward/terminal transitions rejected, cancellation from workflow states, invalid status value rejected.
- `test_order_permissions.py` — anonymous 401, OWNER read 200 / mutations 403, STAFF create 201.
- `test_order_measurement_snapshot.py` — snapshot matches values at creation; snapshot survives a later current-measurement update (v2) and the API serves the historical values.
- `helpers.py` — shared payload/URL/measurement builders reused across files.

### Frontend

Static verification: `npm run lint`, `npx tsc --noEmit`, `npm run build` (all exit 0; non-fatal chunk-size warning unchanged).

## 10. Manual Verification

### Backend

```
Command:  python manage.py check
Result:   System check identified no issues (0 silenced).
Status:   PASS

Command:  python manage.py migrate
Result:   Applying orders.0001_initial... OK
Status:   PASS

Command:  python manage.py migrate --check
Result:   Exit 0 (no missing migrations).
Status:   PASS

Command:  python -m pytest
Result:   183 passed, 0 failed (~77s)
Status:   PASS

Command:  black --check .
Result:   All done! 60 files would be left unchanged.
Status:   PASS

Command:  isort --check-only .
Result:   Exit 0.
Status:   PASS
```

### API integration (automated, via test suite)

```
STAFF: POST   /api/v1/orders/               -> 201 (order_number, status NEW, items, total)
STAFF: POST   /api/v1/orders/{id}/status/   -> 200 through the full CUTTING→…→COLLECTED chain
STAFF: POST   /api/v1/orders/{id}/status/   -> 400 on skip/backward/terminal transitions
STAFF: PATCH  /api/v1/orders/{id}/          -> 200 (notes, expected_delivery_date)
STAFF: PATCH  /api/v1/orders/{id}/          -> status field ignored (stays NEW)
STAFF: DELETE /api/v1/orders/{id}/          -> 405 (no physical delete)
OWNER: GET    /api/v1/orders/               -> 200
OWNER: GET    /api/v1/orders/{id}/          -> 200
OWNER: POST   /api/v1/orders/               -> 403
OWNER: POST   /api/v1/orders/{id}/status/   -> 403
ANON:  GET/POST any order endpoint          -> 401
Measurement snapshot: order created on v1, v2 made current -> item + API still serve v1 snapshot
Status:   PASS
```

### Browser

Browser-based manual verification was not performed in this environment; the API-level integration matrix above (STAFF full walkthrough, OWNER view-only, snapshot immutability) is covered end-to-end by the automated test suite. Interactive browser verification of the new Orders pages is a recommended quick check on first run.

## 11. Known Issues

1. **Vite chunk-size warning (~868 kB).** Non-fatal; code-splitting deferred until more business pages exist (previous phases' note continues).
2. **react-router npm advisory (high, from earlier phases).** `react-router-dom@7.18.x` in the vulnerable range of `GHSA-qwww-vcr4-c8h2`; app uses client-side `BrowserRouter` only. Upgrade when a fixed release exists.
3. **No frontend automated test runner** — frontend verified by static checks + API integration suite, as in earlier phases.
4. **Browser manual verification not run here** — the automated integration matrix covers the flows; see §10.

## 12. Deferred Items

- **Out of Phase 4 scope (explicit):** payments/advances, billing/invoice generation, tailors workload and piece-rate payments, cloth inventory, dashboard/analytics, notifications, digital bills, WhatsApp/SMS.
- **Order editing of customer/items/amounts** — intentionally immutable after creation; recorded order integrity preserved.
- **Physical order deletion** — intentionally not implemented; terminal states (COLLECTED / CANCELLED) only.
- **Measurement snapshot diffing** — items show the snapshot inline; side-by-side version diffing left for a later phase.
- **Multi-currency / taxes / discounts on line items** — single INR unit price for now.

## 13. Files Created/Modified

### Created (backend)

- `apps/orders/__init__.py`, `apps.py`, `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`
- `apps/orders/migrations/0001_initial.py`
- `apps/orders/tests/{__init__.py, helpers.py, test_order_crud.py, test_order_measurement_validation.py, test_order_status.py, test_order_permissions.py, test_order_measurement_snapshot.py}`

### Created (frontend)

- `src/types/orders.ts`
- `src/services/orderService.ts`
- `src/hooks/useOrders.ts`
- `src/pages/Orders.tsx`
- `src/pages/OrderDetail.tsx`
- `src/components/CreateOrderDialog.tsx`

### Modified (backend)

- `config/settings.py` — `apps.orders.apps.OrdersConfig`
- `config/urls.py` — include `apps.orders.urls` under `api/v1/`

### Modified (frontend)

- `src/routes/AppRoutes.tsx` — `/orders` and `/orders/:id` real routes
- `src/pages/Placeholders.tsx` — removed the Orders placeholder (other placeholders unchanged)

### Docs

- `docs/phase-4/PHASE_4_COMPLETION_REPORT.md` — this report

## 14. Git Verification

### Status before commit

Branch `master`; clean except the Phase 4 changes listed in §13 plus the untracked `docs/phase-4/` directory. Remote `origin` = `https://github.com/Vigneshwar-SU/saamu.git`.

### Commit

Commit message: `feat(orders): implement phase 4 order management`

Commit hash: `8b1d2cca199b5a581750ff76b5757f4691967f10`

### Push

Remote/branch: `origin master`

Push result: _(filled in after push)_

## 15. Phase 5 Readiness

**Ready. Phase 4 is PASS and ready for Phase 5.**

- Real order records with a working list/search/detail API and UI, controlled status lifecycle, and full audit history.
- Immutable measurement snapshots keep historical orders correct regardless of later measurement edits.
- Backend RBAC verified end-to-end: OWNER read 200 / mutations 403, STAFF mutations 200/201, anonymous 401; full suite 183 passed.
- Frontend static checks clean; Orders pages follow the same proven vertical-slice pattern (types → service → hooks → pages → dialogs) as earlier phases.
- The full 183-test suite provides a regression baseline for Phase 5.
