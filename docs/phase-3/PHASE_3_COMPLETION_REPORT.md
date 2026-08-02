# Phase 3 Completion Report

## 1. Summary

Phase 3 (Customers & Tailoring Measurements) is complete. The Phase 1 Customers placeholder is replaced by a real, role-aware customer management module backed by a versioned Django REST API, and tailoring measurements (Shirt + Pant, in inches) are recorded with full immutable version history. All 14 acceptance criteria areas from `docs/phase-3/07_PHASE_3_ACCEPTANCE_CRITERIA.md` are satisfied.

Implemented:

- **Customer model + API** — stable integer PK, name/mobile with optional alternate/address/notes, active/archive state, timestamps; list (pagination, search, active/archived/all filter), detail, STAFF create/edit/archive/restore; no physical delete.
- **Measurement model + API** — per-customer, per-garment (SHIRT/PANT) structured values in inches; immutable versioned rows with a current marker; per-garment required/allowed field sets; explicit wrong-field rejection.
- **RBAC** — backend-authoritative: OWNER = view-only, STAFF = full management (reuses Phase 2 `IsOwner`, `IsStaffRole`, `IsOwnerOrStaff`).
- **Frontend** — real Customers list (search / status filter / pagination, STAFF create/edit/archive/restore), a Customer detail page with current measurements + version history + per-garment forms, and OWNER view-only UI.
- **Tests** — backend suite at **140 passed** (all Phase 1/2 tests still green); frontend lint / tsc / build all clean.

Also fixed during this phase: DRF converts a Django `Http404` into a 404 response but leaves the original exception type, so the standardized error handler mapped it to `internal_error`. `apps/common/exceptions.py` now explicitly maps `Http404` → `not_found`, covered by a regression test.

**Final status (post-report verification):** Phase 3 is **PASS and ready for Phase 4**. The items previously environment-blocked were completed and verified: a CORS origin issue was diagnosed and fixed, browser-based manual verification (STAFF walkthrough, OWNER view-only UI, sidebar scrolling) was executed, a sidebar-scroll defect was fixed and verified in-browser, and a full backend RBAC pass (140 tests, 0 failures) reconfirmed OWNER view-only vs STAFF management. No implementation changes were required beyond the fixes described below; none of these changes weakened permissions or altered OWNER/STAFF role semantics.

## 2. Customer Model

`apps/customers/models.py:Customer`:

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField PK | stable internal identifier (no human-friendly code — documented decision) |
| `full_name` | CharField(200) | required |
| `mobile_number` | CharField(16) | required, `^\+?[0-9]{10,15}$` (serializer) |
| `alternate_mobile_number` | CharField(16), blank | optional; must differ from primary; must match mobile regex when present |
| `address` | TextField(1000), blank | whitespace preserved |
| `notes` | TextField(2000), blank | whitespace preserved |
| `is_active` | BooleanField, default True | archive marker; retained rows, restorable |
| `created_at` / `updated_at` | DateTimeField | auto-set |

- `Meta.ordering = ["-id"]`; indexes on `mobile_number` and `is_active`.
- Mobile numbers are **not** globally unique (family/shared phones allowed); the alternate is validated only against the format and against equality with the primary.
- Migration `apps/customers/migrations/0001_initial.py`; applied cleanly; `manage.py migrate --check` passes.

## 3. Customer APIs

All under `/api/v1/`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/v1/customers/` | OWNER + STAFF | List; `?search=&status=active\|archived\|all&page=` |
| GET | `/api/v1/customers/{id}/` | OWNER + STAFF | Detail |
| POST | `/api/v1/customers/` | STAFF | Create |
| PATCH | `/api/v1/customers/{id}/` | STAFF | Edit |
| POST | `/api/v1/customers/{id}/archive/` | STAFF | Set `is_active=False` |
| POST | `/api/v1/customers/{id}/restore/` | STAFF | Set `is_active=True` |

- **Search** is case-insensitive on `full_name` / `mobile_number` / `alternate_mobile_number`; a numeric search term also matches the customer PK.
- **Status filter**: `active` (default), `archived`, `all`. Archived customers remain retrievable via detail and restorable.
- **Pagination**: 20 per page (DRF `PageNumberPagination` default in `common`), response `{count, next, previous, results}`.
- `is_active` is read-only through the serializer — deactivation happens only via the explicit archive/restore actions (both idempotent, return `{success, message}`).
- Validation: required `full_name`/`mobile_number`, mobile format, alternate≠primary, max lengths. Errors use the standardized `{success:false, error:{code,message}}` shape.

## 4. Measurement Model

`apps/customers/models.py:Measurement`:

- FK to `Customer` (`related_name="measurements"`, `on_delete=CASCADE`).
- `garment_type` = TextChoices `SHIRT` / `PANT`.
- `version` (PositiveInteger, default 1) + `is_current` (Boolean, default True).
- Twelve numeric `DecimalField(6,1)` fields (null, blank) via the `inch_field()` helper, all in **inches**, validated 0.1–300.0.
  - Shirt: `neck_circumference`, `chest_circumference`, `waist_circumference`, `shoulder_width`, `sleeve_length`, `sleeve_circumference`, `cuff_circumference`, `shirt_length` (first six required).
  - Pant: `waist_circumference`, `hip_circumference`, `thigh_circumference`, `knee_circumference`, `bottom_circumference`, `length` (first three required).
- `notes` TextField(2000), blank.
- `Meta.ordering = ["garment_type", "version"]`; `UniqueConstraint("customer","garment_type","version")` guards duplicates.

**History strategy (chosen): immutable records + current marker.** Each create/PATCH inserts a new row with `version = max+1` and `is_current = True`, and inside `transaction.atomic` unmarks the previous current row for that (customer, garment_type). Old rows are never mutated, so every historical state is preserved and `is_current` identifies the applicable measurement. A garment type can never change after creation (a "change" creates a new current version of the same garment).

## 5. Measurement APIs

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/v1/customers/{customer_id}/measurements/` | OWNER + STAFF | All versions; `?current=true` returns current rows only |
| POST | `/api/v1/customers/{customer_id}/measurements/` | STAFF | Create next version (201) |
| GET | `/api/v1/measurements/{id}/` | OWNER + STAFF | Any single version |
| PATCH | `/api/v1/measurements/{id}/` | STAFF | Create a new current version for the same garment (201) |

- `customer`, `version`, `is_current`, timestamps are read-only.
- Per-garment validation rejects fields that don't belong to the selected garment and enforces required fields; value range 0.1–300.0 inches; notes ≤ 2000 chars.
- `COERCE_DECIMAL_TO_STRING=False` in settings, so measurements serialize as JSON numbers, not strings.
- Standardized errors throughout (see §3); `Http404` now maps to `not_found` (see §1).

## 6. Permissions

- Backend is authoritative; the frontend's role value is never trusted.
- `CustomerViewSet`: create / partial_update / archive / restore require `IsStaffRole`; list / retrieve require `IsOwnerOrStaff`.
- Measurement views use `IsOwnerOrStaffReadOnly` (read for OWNER+STAFF, mutations STAFF only).
- Verified by integration: OWNER `POST /customers/` → 403; OWNER list → 200; STAFF all mutations → 200/201.
- Anonymous access denied (JWT required) on all endpoints.

## 7. Frontend

- `src/pages/Customers.tsx` — real list replacing the placeholder: debounced search, status filter (Active/Archived/All), 20/page pagination, loading / empty / error + retry states, STAFF-only Add / Edit / Archive / Restore controls, row click → detail.
- `src/pages/CustomerDetail.tsx` — profile card, Active/Archived chip, STAFF edit/archive/restore, measurement chart with Shirt/Pant tabs, current version + chip, version history, per-garment Add/New-Version/Update-from-version flows.
- `src/components/CustomerFormDialog.tsx` — add/edit customer form (react-hook-form + zod: required fields, mobile regex, alternate≠primary, lengths) reused by both pages.
- `src/components/MeasurementFormDialog.tsx` — per-garment numeric entry in inches (required fields per garment, 0.1–300 range, `in` suffix), garment selector on create, locked on update.
- Services/hooks: `customerService`, `measurementService`, `useCustomers`, `useMeasurements` on TanStack Query; list/measurements queries invalidated after mutations.
- OWNER sees view-only UI (no create/edit/archive/add controls).
- Route `/customers/:id` added; `Customers` placeholder removed from `Placeholders.tsx`.

## 8. Tests

Backend: **140 passed** (`python -m pytest`, ~56s) — all 54 Phase 1/2 tests remain green.

- Customer permissions: anonymous 401; OWNER 403 on create/update/archive/restore; STAFF 201/200; archive/restore round-trip.
- Customer validation: required fields, mobile format, alternate≠primary, field lengths, standardized error shape (incl. the new `Http404 → not_found` regression in `apps/common`).
- Customer search/pagination: case-insensitive name/mobile search, numeric-ID search, status filters, 20/page over 25 seeded records.
- Customer archive: row retained, idempotent archive/restore, `updated_at` touched, read-only `is_active` PATCH leaves the row unchanged (DRF silently drops the read-only field).
- Measurement permissions, validation (wrong-garment fields rejected, required per garment, range), history (versions increment, old rows immutable, only one current per garment), and relationships (customer/garment/version constraint, cascade).

Frontend: static verification — `npm run lint`, `npx tsc --noEmit`, `npm run build` (all exit 0).

## 9. Verification Results

### Backend

```
Command:  python manage.py check
Result:   System check identified no issues (0 silenced).
Status:   PASS

Command:  python manage.py migrate --check
Result:   Exit 0 (no missing migrations).
Status:   PASS

Command:  python -m pytest
Result:   140 passed, 0 failed (final run ~57s; all Phase 1/2/3 tests green)
Status:   PASS

Command:  black --check .
Result:   All done! 55 files would be left unchanged. Skipped 3 files.
Status:   PASS

Command:  isort --check-only .
Result:   Exit 0. Skipped 3 files.
Status:   PASS
```

### Backend RBAC verification (final, post-report)

```
Command:  python manage.py check
Result:   System check identified no issues (0 silenced).
Status:   PASS

Command:  python -m pytest
Result:   140 passed, 0 failed
Status:   PASS

OWNER endpoint matrix (integration tests, apps/customers/tests/):
  GET    /api/v1/customers/                     -> 200
  GET    /api/v1/customers/{id}/                -> 200
  GET    /api/v1/customers/{id}/measurements/   -> 200
  GET    /api/v1/measurements/{id}/             -> 200
  POST   /api/v1/customers/                     -> 403
  PATCH  /api/v1/customers/{id}/                -> 403
  POST   /api/v1/customers/{id}/archive/        -> 403
  POST   /api/v1/customers/{id}/restore/        -> 403
  POST   /api/v1/customers/{id}/measurements/   -> 403
  PATCH  /api/v1/measurements/{id}/             -> 403

STAFF regression: create/update/archive/restore customer and create/update
measurement (new version) continue to return 200/201.
Anonymous access to protected endpoints returns 401.
Status:   PASS
```

### Frontend

```
Command:  npm run lint
Result:   Exit 0, no errors/warnings (eslint --max-warnings 0).
Status:   PASS

Command:  npx tsc --noEmit
Result:   Exit 0.
Status:   PASS

Command:  npm run build
Result:   Exit 0. Built in 5.92s. Non-fatal chunk-size warning (819.40 kB) — deferred.
Status:   PASS
```

### Integration (backend :8000 + frontend dev server :5173, via Vite proxy)

```
Command:  POST /api/v1/auth/login/  {staff / Staff@12345}
Result:   200 user.role = STAFF
Status:   PASS

Command:  POST /api/v1/customers/  (STAFF) — new customer
Result:   201 id=1, is_active=True
Status:   PASS

Command:  GET  /api/v1/customers/?search=Integration
Result:   200 count=1, name matched
Status:   PASS

Command:  GET  /api/v1/customers/1/
Result:   200 detail returned
Status:   PASS

Command:  POST /api/v1/customers/1/measurements/  {SHIRT}
Result:   201 version=1, is_current=True, neck=15.5
Status:   PASS

Command:  POST /api/v1/customers/1/measurements/  {PANT}
Result:   201 version=1, is_current=True, length=40.5
Status:   PASS

Command:  PATCH /api/v1/measurements/1/  {SHIRT, updated values}
Result:   201 new version=2, is_current=True; old v1 is_current=False
Status:   PASS

Command:  GET  /api/v1/customers/1/measurements/
Result:   200 3 rows — one current per garment (SHIRT v2, PANT v1)
Status:   PASS

Command:  GET  /api/v1/customers/1/measurements/?current=true
Result:   200 2 rows (SHIRT v2, PANT v1)
Status:   PASS

Command:  POST /api/v1/customers/1/archive/  then  /restore/
Result:   200 archived (is_active=False), 200 restored (is_active=True)
Status:   PASS

Command:  POST /api/v1/customers/  (OWNER)
Result:   403 (view-only enforced)
Status:   PASS

Command:  GET  /api/v1/customers/?search=Integration  (OWNER)
Result:   200 (read allowed)
Status:   PASS
```

### Manual (browser) verification

Interactive-browser verification was executed after the original report (the environment limitation noted earlier was resolved) against the running Vite dev server on its actual origin with the Django backend on :8000.

```
1. CORS during manual verification
   - Frontend ran on the actual Vite origin: http://localhost:5175.
   - Login initially failed: the frontend origin was not correctly allowed by
     the Django CORS configuration.
   - Diagnosed and fixed (config/settings.py CORS_ALLOWED_ORIGINS is
     environment-driven and now includes the actual Vite origin; default covers
     both :5173 and :5175 because the Vite port may drift).
   - Login then verified successfully.
   Status: PASS

2. STAFF manual walkthrough (browser)
   - STAFF login .............................. PASS
   - Customer creation ........................ PASS
   - Customer search .......................... PASS
   - Customer edit ............................ PASS
   - Customer detail .......................... PASS
   - Shirt measurement creation ............... PASS
   - Pant measurement creation ................ PASS
   - Measurement versioning / history ......... PASS
   - Archive .................................. PASS
   - Restore .................................. PASS

3. UI scrolling issue
   - Scrolling failed when the sidebar was OPEN.
   - Diagnosed as a sidebar/MainLayout interaction: the mobile temporary Drawer
     (a MUI Modal) shared the `open` state on desktop, so MUI's Modal scroll-lock
     set `body { overflow: hidden }` and blocked document scrolling.
   - Layout corrected in src/components/Sidebar.tsx (temporary drawer's open
     state gated behind the `md` breakpoint).
   - Scrolling with sidebar OPEN verified; scrolling with sidebar CLOSED also
     verified.
   Status: PASS

4. OWNER verification (browser)
   - OWNER can view customer data ............. PASS
   - OWNER can search and open customer detail  PASS
   - OWNER can view measurements and history .. PASS
   - OWNER mutation controls unavailable in UI  PASS
```

## 10. Commands Executed

```
cd backend
.\.venv\Scripts\activate
python manage.py makemigrations customers
python manage.py migrate
python manage.py check
python manage.py migrate --check
python -m pytest
python -m black --check .
python -m isort --check-only .
python manage.py runserver 127.0.0.1:8000 --noreload   # restarted to load Phase 3 code

cd frontend
npm run lint
npx tsc --noEmit
npm run build

# Integration through the Vite proxy (PowerShell Invoke-RestMethod):
# login → create customer → search → detail → create SHIRT/PANT → PATCH new SHIRT
# version → history/current-only checks → archive/restore → OWNER 403 on create, 200 on list

# Final verification (post-report):
python manage.py check            # 0 issues
python -m pytest                  # 140 passed, 0 failed
# Manual browser verification against the actual Vite origin (http://localhost:5175)
# with Django on :8000:
#   CORS login fix -> STAFF walkthrough (create/search/edit/detail, SHIRT/PANT,
#   versioning/history, archive/restore) -> sidebar OPEN/CLOSED scroll fix ->
#   OWNER view-only (data/search/detail/measurements/history, no mutation controls)
```

## 11. Files Created/Modified

### Created (backend)

- `apps/customers/__init__.py`, `apps.py`, `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`
- `apps/customers/migrations/0001_initial.py`
- `apps/customers/tests/{__init__.py, helpers.py, test_customer_permissions.py, test_customer_validation.py, test_customer_search_pagination.py, test_customer_archive.py, test_measurement_permissions.py, test_measurement_validation.py, test_measurement_history.py, test_measurement_relationships.py}`

### Created (frontend)

- `src/types/customers.ts`
- `src/services/customerService.ts`
- `src/services/measurementService.ts`
- `src/hooks/useCustomers.ts`
- `src/hooks/useMeasurements.ts`
- `src/pages/Customers.tsx`
- `src/pages/CustomerDetail.tsx`
- `src/components/CustomerFormDialog.tsx`
- `src/components/MeasurementFormDialog.tsx`

### Modified (backend)

- `config/settings.py` — `apps.customers.apps.CustomersConfig`; `COERCE_DECIMAL_TO_STRING: False`
- `config/urls.py` — include `apps.customers.urls` under `api/v1/`
- `apps/common/exceptions.py` — `Http404` → `not_found` in the exception code map
- `apps/common/tests/test_error_handling.py` — `test_django_http404_error_shape` regression test

### Modified (frontend)

- `src/routes/AppRoutes.tsx` — real `Customers` page + `/customers/:id` detail route
- `src/pages/Placeholders.tsx` — removed the Customers placeholder (other placeholders unchanged)

### Fixed during final verification (post-report)

- `config/settings.py` — `CORS_ALLOWED_ORIGINS` is environment-driven and now includes the actual Vite origin used during manual verification (`:5175` alongside `:5173`). Previously the running frontend origin was not allowed, which broke login; fixed and login re-verified. (CORS middleware/deps were already present from Phase 1.)
- `src/components/Sidebar.tsx` — mobile temporary Drawer's `open` state is now gated behind the `md` breakpoint so the temporary Drawer Modal (a MUI Modal) stays closed on desktop. Before the fix, its scroll-lock set `body { overflow: hidden }` and blocked document scrolling while the sidebar was open. Scrolling verified with the sidebar OPEN and CLOSED.

### Docs

- `README.md` — current stage, new Customers & Measurements section, repository layout, phase status
- `docs/phase-3/PHASE_3_COMPLETION_REPORT.md` — this report

## 12. Known Issues

1. **Latent error-mapping bug fixed in Phase 3.** DRF converts Django's `Http404` into a 404 response but leaves the original exception type, so the standardized error handler previously reported `internal_error` instead of `not_found` for 404s raised via `get_object_or_404`. Explicitly mapped in `apps/common/exceptions.py`; regression-tested.
2. **Running dev backend was stale.** The pre-existing `runserver` process (started before the customers app existed) had to be restarted to serve the new routes. If the API 404s after a fresh pull, restart the Django server.
3. **Vite chunk-size warning (~819 kB).** Non-fatal; code-splitting deferred until more business pages exist (Phase 2 note continues).
4. **react-router npm advisory (high, from Phase 1/2).** `react-router-dom@7.18.x` in the vulnerable range of `GHSA-qwww-vcr4-c8h2`; the app uses client-side `BrowserRouter` only. Upgrade when a fixed release exists.
5. **Custom 404/500 JSON handlers active only when `DEBUG=False`** (Phase 1 note, unchanged).
6. **No frontend automated test runner** — frontend verified by static checks + live integration harness + browser-based manual verification, as in Phases 1–2.

## 13. Deferred Items

- **Out of Phase 3 scope (explicit):** Orders, Garments, cloth inventory, Tailors, workload, salary, income, expenses, payments, locker/collection workflow, digital bills, WhatsApp/SMS, dashboard/reporting, notifications.
- **Physical customer deletion** — intentionally not implemented; archive/restore only.
- **Human-friendly customer codes** — intentionally not implemented; stable integer `id` is the identifier.
- **Multi-unit measurements** — inches only for the first version (documented decision).
- **Measurement "history diff" view** — history is browsable per version; side-by-side diffing is left for a later phase.

## 14. Phase 4 Readiness

**Ready. Phase 3 is PASS and ready for Phase 4.**

Phase 3 final state:

- Real customer records with stable IDs and a working list/search/detail API and UI.
- Versioned measurement data per customer/garment, ready to snapshot onto an order.
- Backend RBAC verified end-to-end: OWNER read → 200, OWNER mutations → 403, STAFF mutations → 200/201, anonymous → 401; full suite 140 passed, 0 failed.
- Browser-based manual verification green: CORS login, STAFF walkthrough, sidebar scrolling (OPEN and CLOSED), OWNER view-only UI.
- A proven, reusable vertical slice: model → migration → serializer → viewset → RBAC → tests → frontend page/hook/dialog — the same pattern can be replicated for orders, tailors, income, and expenses.
- The full test suite (140) and static frontend checks as a regression baseline.
