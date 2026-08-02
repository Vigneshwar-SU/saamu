# Phase 5 Completion Report

## 1. Summary

Status: **PASS**

Phase 5 (Tailors, Workload & Piece-Rate Salary) is complete. A new `apps/tailors` Django app adds tailor profiles (archive/restore, no delete), per-garment piece rates, work assignments with a controlled status lifecycle, and computed piece-rate earnings. The Orders module gained additive `assigned_quantity` / `remaining_quantity` exposure on order items. The frontend replaces the Tailors placeholder with a real, role-aware module: Tailors list (search / scope filter / pagination / earnings summary + piece-rate manager), Tailor detail (profile, earnings by garment, work assignments with progress + status actions, assign-work dialog). All Phase 5 scope items from `docs/phase-5/01_PHASE_5_SCOPE.md` are implemented; Phase 6+ items (attendance, payroll, salary transfers, tax/PF/ESI, leave, notifications, dashboard analytics, income/expense, payments, billing) are explicitly deferred.

**Final status:** Phase 5 is **PASS and ready for Phase 6**.

## 2. Features Implemented

- **Tailor management** — create/edit tailor profiles (`name` required, optional mobile / notes), archive/restore (no physical delete). Archived tailors can no longer receive new assignments but their historical assignments remain intact and visible.
- **Piece rates** — configure a rate per garment type; `garment_type` is unique, `rate_per_piece` is a non-negative decimal. Rates are never deleted — deactivated instead. Inactive rates cannot be used for new assignments.
- **Work assignment** — assign part or all of an order item's remaining quantity to an active tailor. The applicable active piece rate is snapshotted at assignment time. Remaining quantity is validated under a `select_for_update` row lock so concurrent assignments never over-allocate. Multiple assignments consume an item's remaining quantity.
- **Status lifecycle** — `ASSIGNED → IN_PROGRESS → COMPLETED`, backend-enforced and terminal at COMPLETED. `started_at` / `completed_at` are set automatically. `completed_quantity` is reportable on the way (0..assigned) and baked in at completion.
- **Earnings** — `earned_amount = completed_quantity × rate_per_piece_snapshot`. Later piece-rate edits never alter historical earnings. Earnings endpoints expose per-garment breakdowns and a cross-tailor summary including outstanding (unfinished) workload.
- **RBAC** — backend-authoritative: OWNER = view-only (list / detail / earnings / summary), STAFF = all mutations (create / safe PATCH / archive-restore / status transitions / completed quantity).
- **Frontend** — Tailors list, Tailor detail, piece-rate manager, assign-work dialog, report-progress dialog, and per-assignment status actions; all mutation controls hidden for OWNER.

## 3. Data Model

All in `apps/tailors/models.py` (migration `apps/tailors/migrations/0001_initial.py`), extending `apps/common/models.py` which now defines the abstract `TimeStampedModel` (`created_at` / `updated_at`) and a `now()` helper.

**`Tailor`**:

| Field | Type | Notes |
|---|---|---|
| `full_name` | CharField(200) | required |
| `mobile_number` | CharField(16), blank | 10–15 digits, optional leading `+` |
| `notes` | TextField, blank | |
| `is_active` | BooleanField | default `True`; archive/restore actions only |
| `created_at` / `updated_at` | DateTimeField | inherited from `TimeStampedModel` |

- `Meta.ordering = ["-created_at"]`. No delete path; archive sets `is_active = False`.

**`PieceRate`**:

| Field | Type | Notes |
|---|---|---|
| `garment_type` | CharField(50), unique | |
| `rate_per_piece` | DecimalField(12,2) | `MinValueValidator(0)`, INR per piece |
| `is_active` | BooleanField | default `True`; used by assignment creation |
| timestamps | | from `TimeStampedModel` |

**`WorkAssignment`**:

| Field | Type | Notes |
|---|---|---|
| `tailor` | FK Tailor (PROTECT) | active-only at creation |
| `order_item` | FK OrderItem (PROTECT) | must belong to the referenced order |
| `assigned_quantity` | PositiveInteger | `MinValueValidator(1)`, ≤ remaining |
| `completed_quantity` | PositiveInteger | default 0, ≤ assigned |
| `status` | CharField(20) | `ASSIGNED` / `IN_PROGRESS` / `COMPLETED` |
| `rate_per_piece_snapshot` | DecimalField(12,2) | immutable copy of the rate at creation |
| `assigned_at` | DateTimeField | `auto_now_add` |
| `started_at` / `completed_at` | DateTimeField, null | set by `advance_status` |
| `created_by` | FK User (PROTECT), null | staff who created it |

- `earned_amount` / `remaining_quantity` are properties (`completed × snapshot`, `assigned − completed`).
- `ALLOWED_TRANSITIONS = {ASSIGNED: {IN_PROGRESS}, IN_PROGRESS: {COMPLETED}}`; `advance_status(to_status)` applies the transition atomically and stamps timestamps.
- `Meta.ordering = ["-assigned_at"]`.

## 4. API Endpoints

All under `/api/v1/` (router + explicit summary route in `apps/tailors/urls.py`).

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET / POST | `/tailors/` | read OWNER+STAFF / create STAFF | List (search, scope, page) / create |
| GET / PATCH | `/tailors/{id}/` | read OWNER+STAFF / edit STAFF | Detail / safe edit |
| POST | `/tailors/{id}/archive/` | STAFF | Archive (blocks new assignments) |
| POST | `/tailors/{id}/restore/` | STAFF | Restore |
| GET / POST | `/piece-rates/` | read OWNER+STAFF / create STAFF | List / create |
| PATCH | `/piece-rates/{id}/` | STAFF | Edit rate or active flag (no delete) |
| GET / POST | `/work-assignments/` | read OWNER+STAFF / create STAFF | List / assign |
| GET / PATCH | `/work-assignments/{id}/` | read OWNER+STAFF / report STAFF | Detail / `completed_quantity` |
| POST | `/work-assignments/{id}/status/` | STAFF | Status transition (optional `completed_quantity` on completion) |
| GET | `/tailors/{id}/earnings/` | OWNER+STAFF | Per-tailor earnings + garment breakdown |
| GET | `/tailor-earnings/summary/` | OWNER+STAFF | Aggregate earnings + outstanding workload |

- **List filters** — tailors: `search` (name/mobile icontains), `scope=active|archived|all`; work assignments: `tailor`, `order`, `garment_type`, `status`, `date_from`, `date_to`; earnings: `date_from`, `date_to`, `garment_type` (detail) and `tailor` (summary). All lists paginated at 20/page.
- **Error contract** — consistent `{success:false, error:{code, message, details?}}` from `apps/common/exceptions.py`.
- **Order additive change** — `OrderItemSerializer` now exposes `assigned_quantity` / `remaining_quantity` (computed from `obj.work_assignments`); `OrderViewSet` prefetches `items__work_assignments`.

## 5. RBAC Verification

Backend-enforced via `IsOwnerOrStaff` / `IsStaffRole`, gated per `self.action` (`TAILOR_MUTATION_ACTIONS = {"create","partial_update","archive","restore"}`, plus piece-rate and assignment mutation sets). Verified by integration tests:

- Anonymous: 401 on all tailors/piece-rates/assignments endpoints.
- OWNER: list/detail/earnings/summary 200; POST/PATCH/archive/restore/status → 403.
- STAFF: all mutations succeed (201/200); reads succeed.
- Live API smoke test (runserver + HTTP): STAFF login → create tailor (201), create piece rate (201), reads OK; OWNER login → tailor read OK, tailor create → 403.

## 6. Frontend

New vertical slice following the established pattern (types → service → hooks → components/dialogs → pages → routes):

- `types/tailors.ts` — Tailor, PieceRate, WorkAssignment (+ statuses, labels, colors, next-status map), earnings types, payloads/params.
- `services/tailorService.ts` — `tailorService` (list/get/create/update/archive/restore/earnings/earningsSummary), `pieceRateService`, `workAssignmentService` (reportProgress, changeStatus).
- `hooks/useTailors.ts` — list/get/mutations for tailors, piece rates, work assignments; earnings + earnings-summary queries; earnings invalidation on assignment mutations.
- `components/TailorFormDialog.tsx` — react-hook-form + zod create/edit dialog.
- `components/PieceRateDialog.tsx` — view/add/edit rate + activate/deactivate.
- `components/AssignWorkDialog.tsx` — active-tailor select, order search + detail fetch, eligible item select (remaining qty), quantity, applicable-rate hint.
- `pages/Tailors.tsx` — list with search/scope/pagination, earnings summary strip, add/edit, archive/restore, piece-rate manager entry.
- `pages/TailorDetail.tsx` — profile, earnings breakdown by garment, work-assignment table with status filter, report-progress dialog, advance-status actions, assign-work dialog.
- Routes: `/tailors` and `/tailors/:id` wired in `AppRoutes.tsx`; Tailors removed from `Placeholders.tsx`.
- `types/orders.ts` — `OrderItem` gains `assigned_quantity` / `remaining_quantity`.

OWNER sees no mutation controls (UI + backend enforcement).

## 7. Tests

Backend (all pass):

```text
python manage.py check                        → clean
python manage.py migrate --check              → exit 0
python -m pytest                              → 254 passed (baseline 183 → 254)
python -m black --check apps/ config/         → 83 files unchanged, 0 to reformat
python -m isort --check-only apps/ config/    → clean
```

New test files in `apps/tailors/tests/`: `helpers.py`, `test_tailors_crud.py`, `test_tailors_permissions.py`, `test_piece_rates.py`, `test_work_assignments.py`, `test_assignment_status.py`, `test_earnings.py`. Coverage matches the acceptance list: anonymous denied; OWNER read/mutation split; STAFF create/edit/archive/restore; archived-tailor assignment rejection; historical assignment retention; valid/invalid assignments; customer–order-item mismatch rejection; quantity bounds (≤0, above remaining); multiple assignments consuming remaining; completed ≤ assigned; valid/invalid status transitions; rate snapshot + later-edit invariance; earnings = completed × snapshot; date/tailor/garment filters; OWNER+STAFF earnings reads.

Frontend (all pass):

```text
npm run lint      → clean
npx tsc --noEmit  → clean
npm run build     → built (chunk-size warning only, pre-existing)
```

## 8. Manual Verification

### STAFF

Live API walkthrough (Django runserver on 127.0.0.1 + HTTP requests) covering the staff flow:

1. Login STAFF → access token issued, role `STAFF`.
2. Create tailor `Smoke Test Tailor` → 201, id returned.
3. Configure piece rate SHIRT @ 125.50 → 201.
4. Search tailors (`?search=Smoke`) → count 1.
5. List work assignments → 200 (empty at the time).
6. Earnings summary → `success=True` with totals + per-tailor rows.

Assignment creation, remaining-quantity consumption, progress reporting, and status transitions (steps 5–10 of the documented walkthrough) are exercised by the integration tests (`test_work_assignments.py`, `test_assignment_status.py`, `test_earnings.py`) using the DRF test client against the real URL routes, including the `select_for_update` remaining check and archived-tailor rejection.

### OWNER

1. Login OWNER → access token issued, role `OWNER`.
2. Tailor list read → 200 (count matches).
3. Tailor create attempt → **403 Forbidden** (mutation blocked).
4. Frontend hides mutation controls for OWNER (static review; same pattern as Phases 3–4).

### Regression

Full backend suite (254 tests) includes all Phase 1–4 tests (customers, measurements, orders, auth/RBAC), which remain green. Frontend `lint`/`tsc`/`build` clean with the Orders/Customers pages untouched by new routing. Orders detail now renders assigned/remaining quantities per item.

## 9. Known Issues

- Frontend production build emits a chunk-size warning (>500 kB after minification); pre-existing and non-blocking (no code-splitting added in this phase).
- Assignment creation rejects work for garments without an active piece rate; the assign dialog surfaces the required rate hint (intended behavior).

## 10. Deferred Items

Explicitly out of scope for Phase 5 (per `docs/phase-5/01_PHASE_5_SCOPE.md`) and not implemented: tailor attendance, payroll, salary transfers, tax/PF/ESI, leave, notifications, dashboard analytics, income/expense, payments, billing, invoice generation. Piece-rate snapshot history (rate audit trail beyond the snapshot on each assignment) is also deferred.

## 11. Files Created/Modified

**Created — backend:**
- `backend/apps/tailors/__init__.py`, `apps.py`, `admin.py`, `models.py`, `serializers.py`, `views.py`, `urls.py`
- `backend/apps/tailors/migrations/0001_initial.py`
- `backend/apps/tailors/tests/helpers.py`, `test_tailors_crud.py`, `test_tailors_permissions.py`, `test_piece_rates.py`, `test_work_assignments.py`, `test_assignment_status.py`, `test_earnings.py`
- `backend/apps/common/models.py` (`TimeStampedModel` + `now`)

**Modified — backend:**
- `backend/apps/orders/serializers.py` — expose `assigned_quantity` / `remaining_quantity`
- `backend/apps/orders/views.py` — prefetch `items__work_assignments`
- `backend/config/settings.py` — register `apps.tailors`
- `backend/config/urls.py` — include `apps.tailors.urls` under `/api/v1/`

**Created — frontend:**
- `frontend/src/types/tailors.ts`
- `frontend/src/services/tailorService.ts`
- `frontend/src/hooks/useTailors.ts`
- `frontend/src/components/TailorFormDialog.tsx`, `PieceRateDialog.tsx`, `AssignWorkDialog.tsx`
- `frontend/src/pages/Tailors.tsx`, `TailorDetail.tsx`

**Modified — frontend:**
- `frontend/src/types/orders.ts` — add `assigned_quantity` / `remaining_quantity`
- `frontend/src/routes/AppRoutes.tsx` — `/tailors` + `/tailors/:id`
- `frontend/src/pages/Placeholders.tsx` — remove Tailors placeholder

**Documentation:**
- `README.md` — current stage → Phase 5; new Tailors/Piece-Rates/Assignments section; repo layout + phase status updates
- `docs/phase-5/` — the nine Phase 5 planning/specification documents (committed) and this report

## 12. Git Verification

### Status before commit

Branch `master`; remote `origin` = `https://github.com/Vigneshwar-SU/saamu.git`. Working tree contained only the Phase 5 changes listed in §11 plus the untracked `docs/phase-5/` directory.

### Commit

Commit message: `feat(tailors): implement phase 5 tailor workload and piece-rate salary`

Commit hash: `bd34df811663d59b3cf679c9857c14d4dc9e92d8` (short `bd34df8`).

### Push

Remote/branch: `origin master`

Push result: **Pushed.** `caf00db..bd34df8 master -> master`. Verified after push: `git rev-parse HEAD` == `git rev-parse origin/master` and `git status` reports "up to date with 'origin/master'" with a clean working tree (the report commit follows).

## 13. Phase 6 Readiness

**Ready. Phase 5 is PASS and ready for Phase 6.**

- Real tailor profiles, piece rates, and work assignments with backend-enforced lifecycle, remaining-quantity integrity (row-locked), and immutable rate snapshots.
- Earnings computed and surfaced at the tailor and cross-tailor level, including outstanding workload.
- RBAC verified end-to-end by integration tests and a live API smoke test: OWNER read 200 / mutation 403, STAFF mutations 201/200, anonymous 401; full suite 254 passed.
- Frontend static checks clean; the Phase 5 UI follows the proven vertical-slice pattern.
- The full 254-test suite provides the regression baseline for Phase 6.
