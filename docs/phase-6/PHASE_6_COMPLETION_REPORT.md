# Phase 6 Completion Report

## 1. Summary

Status: **PASS**

Phase 6 (Attendance + Payroll Foundation) is complete. Two new Django apps are added:

- `apps/attendance` — daily tailor attendance records (`PRESENT` / `ABSENT` / `HALF_DAY`) with duplicate `(tailor, attendance_date)` protection, notes, and a `marked_by` audit trail. Reads are available to OWNER and STAFF; create/edit is STAFF-only.
- `apps/payroll` — piece-rate payroll periods (`DRAFT → CALCULATED → FINALIZED`) and per-tailor payroll entries. Earnings are computed exclusively from completed `WorkAssignment`s inside the period using the immutable `rate_per_piece_snapshot` (`completed_quantity × snapshot`); in-progress/outstanding pieces and missing attendance contribute zero. Attendance is aggregated per tailor (present/half-day/absent days) with `attendance_amount` remaining `0` since no monetary attendance rule is configured.

The frontend replaces the Payroll placeholder with real, role-aware pages: Attendance list (date/tailor/status filters + pagination, mark/edit records), Payroll period list (status, aggregates, calculate/finalize actions), and Payroll detail (summary cards, tailor entries table, and a tailor-level assignment breakdown that links to `GET /payroll/periods/{id}/tailors/{tailor_id}/`). Sidebar gains Attendance and Payroll entries.

All Phase 6 scope items from `docs/phase-6/01_PHASE_6_SCOPE.md` are implemented; Phase 7+ items (salary transfers/payments, tax/PF/ESI, leave, notifications, dashboard analytics, income/expense, billing) remain explicitly deferred.

**Final status:** Phase 6 is **PASS and ready for Phase 7**.

## 2. Features Implemented

- **Attendance marking** — STAFF records a tailor's daily status (`PRESENT`, `ABSENT`, `HALF_DAY`) with optional notes; the authenticated user is stored as `marked_by`. The `(tailor, attendance_date)` pair is unique, so a tailor has exactly one record per date. Records are never deleted — they can only be edited while still required.
- **Attendance list** — paginated list with filters for `tailor`, `date_from`, `date_to` and `status`; archived tailors remain visible in both filters and results (their historical records are never hidden).
- **Payroll periods** — STAFF creates a period with `period_start` / `period_end` (end on/after start, DB-check-constrained) and optional notes. Lifecycle is `DRAFT → CALCULATED → FINALIZED`; FINALIZED is immutable through normal operations.
- **Calculation** — `calculate()` aggregates completed assignments and attendance into one `PayrollEntry` per tailor. Inclusion is driven by `WorkAssignment.completed_at` with inclusive boundaries (`period_start <= completion_date <= period_end`). Entries are replaced on each recalculation while the period is editable; FINALIZED periods reject recalculation.
- **Earnings rule** — `piece_rate_earnings = completed_quantity × rate_per_piece_snapshot` per assignment, summed per tailor. The snapshot is the immutable copy taken at assignment time, so later piece-rate edits never alter historical payroll.
- **Attendance in payroll** — `present_days` / `half_days` / `absent_days` are counted per tailor from records inside the period. Missing attendance is never treated as PRESENT. `attendance_amount` stays `0` (no invented monetary rule) and `total_payable == piece_rate_earnings`.
- **Tailor-level breakdown** — for any tailor in a period, the API returns the entry summary plus the individual completed assignments (order number, garment, assigned/completed/remaining, rate snapshot, earned amount).
- **RBAC** — backend-authoritative: OWNER = read only (periods, entries, tailor detail); STAFF = all mutations (create period, calculate, finalize, attendance create/edit); anonymous = 401.

## 3. Data Model

### `apps/attendance/models.py` (migration `0001_initial.py`)

**`Attendance`**:

| Field | Type | Notes |
|---|---|---|
| `tailor` | FK Tailor (PROTECT) | `related_name="attendance_records"` |
| `attendance_date` | DateField | |
| `status` | CharField(10) | `PRESENT` / `ABSENT` / `HALF_DAY` |
| `notes` | TextField, blank | |
| `marked_by` | FK AUTH_USER_MODEL (SET_NULL), null | audited marker |
| timestamps | | from `TimeStampedModel` |

- `UniqueConstraint(fields=["tailor", "attendance_date"])` enforced at DB and serializer level (duplicate error surfaces on `attendance_date`).
- `Meta.ordering = ["-attendance_date", "-created_at"]`. No delete path.

### `apps/payroll/models.py` (migration `0001_initial.py`)

**`PayrollPeriod`**:

| Field | Type | Notes |
|---|---|---|
| `period_start` / `period_end` | DateField | inclusive bounds |
| `status` | CharField(20) | `DRAFT` / `CALCULATED` / `FINALIZED` |
| `notes` | TextField, blank | |
| `created_by` | FK AUTH_USER_MODEL (SET_NULL), null | |
| timestamps | | from `TimeStampedModel` |

- `CheckConstraint` `period_start <= period_end`; `Index` on `(period_start, period_end)` and `status`.
- `completed_assignments()` filters `WorkAssignment.status=COMPLETED` and `completed_at__date` in `[period_start, period_end]`.
- `calculate()` runs in a transaction: deletes prior entries, aggregates pieces/earnings from completed assignments, counts attendance days per tailor, builds one `PayrollEntry` per tailor with any work or attendance, `bulk_create`s them, and moves the period to `CALCULATED`. Raises `ValidationError` for FINALIZED periods.

**`PayrollEntry`**:

| Field | Type | Notes |
|---|---|---|
| `payroll_period` | FK PayrollPeriod (CASCADE) | `related_name="entries"` |
| `tailor` | FK Tailor (PROTECT) | |
| `present_days` / `half_days` / `absent_days` | PositiveInteger | default 0 |
| `completed_pieces` | PositiveInteger | default 0 |
| `piece_rate_earnings` | Decimal(12,2) | sum of `completed × snapshot` |
| `attendance_amount` | Decimal(12,2) | default `0.00` (no rule in Phase 6) |
| `total_payable` | Decimal(12,2) | `piece_rate_earnings + attendance_amount` |

- `UniqueConstraint(fields=["payroll_period", "tailor"])`; `Index` on `(payroll_period, tailor)`. Entries are replaced, never edited, during recalculation; no physical deletion of payroll history is exposed.

## 4. API Endpoints

All under `/api/v1/`. Error contract is the standard `{success:false, error:{code, message, details?}}`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET / POST | `/attendance/` | read OWNER+STAFF / create STAFF | List (tailor, date_from, date_to, status, page) / create |
| GET / PATCH | `/attendance/{id}/` | read OWNER+STAFF / edit STAFF | Detail / safe edit |
| GET / POST | `/payroll/periods/` | read OWNER+STAFF / create STAFF | List / create |
| GET | `/payroll/periods/{id}/` | OWNER+STAFF | Detail with aggregates |
| POST | `/payroll/periods/{id}/calculate/` | STAFF | Generate entries → CALCULATED (re-runnable while editable) |
| POST | `/payroll/periods/{id}/finalize/` | STAFF | Lock period → FINALIZED |
| GET | `/payroll/entries/` | OWNER+STAFF | Entries with `period` / `tailor` filters |
| GET | `/payroll/periods/{id}/tailors/{tailor_id}/` | OWNER+STAFF | Tailor entry + assignment breakdown |

- **Period aggregates** — list/detail responses include `total_completed_pieces`, `total_piece_rate_earnings`, `total_attendance_amount`, `total_payable`, `entry_count`, plus `created_by_name`.
- **Attendance response** — nested tailor object plus `marked_by_name`.
- All lists paginated at 20/page.

## 5. RBAC Verification

Backend-enforced via `IsOwnerOrStaff` / `IsStaffRole`, gated per `self.action` (`ATTENDANCE_MUTATION_ACTIONS = {"create","partial_update"}`, `PAYROLL_PERIOD_MUTATION_ACTIONS = {"create","calculate","finalize"}`). Verified by integration tests:

- Anonymous: 401 on attendance and payroll endpoints.
- OWNER: list/detail 200; attendance create/edit, period create/calculate/finalize → 403.
- STAFF: attendance create/edit, period create, calculate, finalize all succeed (201/200); reads succeed.

## 6. Frontend

New vertical slices following the established pattern (types → service → hooks → dialogs → pages → routes):

- `types/attendance.ts` — Attendance, statuses (labels/colors), list params/result, payload.
- `types/payroll.ts` — PayrollPeriod (+ status labels/colors + aggregates), PayrollEntry, PayrollAssignment, tailor-detail and action response types.
- `services/attendanceService.ts` — list/create/update.
- `services/payrollService.ts` — listPeriods/getPeriod/createPeriod/calculate/finalize/listEntries/tailorDetail.
- `hooks/useAttendance.ts` — list/create/update with query invalidation.
- `hooks/usePayroll.ts` — period list/detail, create/calculate/finalize mutations, entries and tailor-detail queries with cache invalidation.
- `components/AttendanceFormDialog.tsx` — react-hook-form + zod create/edit dialog (tailor select, date, status, notes); tailor locked on edit.
- `components/PayrollPeriodDialog.tsx` — react-hook-form + zod create dialog (period range with end>=start validation, notes).
- `pages/Attendance.tsx` — list with date range / tailor / status filters, pagination, mark/edit actions (STAFF only), status chips, marked-by column.
- `pages/Payroll.tsx` — period list with status chips, aggregate columns, Calculate (DRAFT) / Finalize (CALCULATED) actions with confirm dialogs, row navigation to detail.
- `pages/PayrollDetail.tsx` — summary cards, notes, tailor entries table, click a tailor row to expand the assignment-breakdown table (fetches the tailor-detail endpoint).
- `constants/navigation.ts` — Attendance and Payroll sidebar items; `routes/AppRoutes.tsx` — `/attendance`, `/payroll`, `/payroll/:id`.

OWNER sees no mutation controls (UI + backend enforcement).

## 7. Tests

Backend (all pass):

```text
python manage.py check                        → clean
python manage.py migrate --check              → exit 0
python -m pytest                              → 291 passed (baseline 254 → 291)
python -m black --check apps/ config/         → 103 files unchanged, 0 to reformat
python -m isort --check-only apps/ config/    → clean
```

New test files: `apps/attendance/tests/helpers.py` + `test_attendance.py` (14 tests) and `apps/payroll/tests/helpers.py` + `test_payroll.py` (19 tests). Coverage: anonymous 401; OWNER read / mutation 403 split; STAFF create/edit; all attendance statuses; duplicate `(tailor, date)` rejected at API and ORM level; invalid status rejected; tailor/status/date-range filters + invalid filter status; archived-tailor visibility; payroll period creation + invalid date range; period aggregates; completed-only inclusion (IN_PROGRESS/outstanding excluded); inclusive boundary dates; historical rate-snapshot invariance after current-rate change; multi-tailor aggregation; attendance day aggregation with `attendance_amount == 0`; recalculation while editable; FINALIZED recalculation blocked; finalize requires CALCULATED; finalize works and blocks re-finalize; entries period/tailor filters; tailor-detail assignment breakdown; OWNER entries/tailor-detail reads; archived-tailor payroll history.

Frontend (all pass):

```text
npm run lint      → clean
npx tsc --noEmit  → clean
npm run build     → built (chunk-size warning only, pre-existing)
```

## 8. Manual Verification

The payroll/attendance flows (period create → calculate → finalize, duplicate attendance rejection, boundary/rate-snapshot arithmetic, RBAC) are exercised end-to-end by the integration tests through the real URL routes with the DRF test client. Frontend behavior is covered by the static build checks; the UI follows the proven Phase 3–5 vertical-slice patterns.

## 9. Known Issues

- Frontend production build emits a pre-existing chunk-size warning (>500 kB after minification); non-blocking.
- `attendance_amount` is always `0` because no monetary attendance rule is configured (intended per `docs/phase-6/04_PHASE_6_PAYROLL_RULES.md`); the column and API surface are ready for a future rule.

## 10. Deferred Items

Explicitly out of scope for Phase 6 (per `docs/phase-6/09_PHASE_6_DEFERRED_AND_GUARDRAILS.md`) and not implemented: salary transfers / advance / payment against payroll, attendance-based monetary amounts, tax/PF/ESI deductions, leave management, notifications, dashboard analytics, income/expense, payments/billing, and a payroll period wizard. Finalized-period reversal/unfinalize is intentionally unsupported (immutability guardrail).

## 11. Files Created/Modified

**Created — backend:**
- `backend/apps/attendance/__init__.py`, `apps.py`, `admin.py`, `models.py`, `serializers.py`, `views.py`, `urls.py`
- `backend/apps/attendance/migrations/0001_initial.py`
- `backend/apps/attendance/tests/helpers.py`, `test_attendance.py`
- `backend/apps/payroll/__init__.py`, `apps.py`, `admin.py`, `models.py`, `serializers.py`, `views.py`, `urls.py`
- `backend/apps/payroll/migrations/0001_initial.py`
- `backend/apps/payroll/tests/helpers.py`, `test_payroll.py`

**Modified — backend:**
- `backend/config/settings.py` — register `apps.attendance` + `apps.payroll`
- `backend/config/urls.py` — include attendance + payroll routers under `/api/v1/`
- `backend/apps/tailors/views.py` — black-format collapse (no behavior change)

**Created — frontend:**
- `frontend/src/types/attendance.ts`, `frontend/src/types/payroll.ts`
- `frontend/src/services/attendanceService.ts`, `frontend/src/services/payrollService.ts`
- `frontend/src/hooks/useAttendance.ts`, `frontend/src/hooks/usePayroll.ts`
- `frontend/src/components/AttendanceFormDialog.tsx`, `frontend/src/components/PayrollPeriodDialog.tsx`
- `frontend/src/pages/Attendance.tsx`, `frontend/src/pages/Payroll.tsx`, `frontend/src/pages/PayrollDetail.tsx`

**Modified — frontend:**
- `frontend/src/constants/navigation.ts` — Attendance + Payroll sidebar items
- `frontend/src/routes/AppRoutes.tsx` — `/attendance`, `/payroll`, `/payroll/:id`

**Documentation:**
- `docs/phase-6/` — the nine Phase 6 planning/specification documents (committed) and this report

## 12. Git Verification

### Commit

Commit message: `feat(payroll): implement phase 6 attendance and payroll`

### Push

Remote/branch: `origin master`. After push: `git rev-parse HEAD` == `git rev-parse origin/master` and `git status` reports a clean working tree.

## 13. Phase 7 Readiness

**Ready. Phase 6 is PASS and ready for Phase 7.**

- Attendance records exist with uniqueness protection and a full audit trail; archived tailors remain visible.
- Payroll periods follow `DRAFT → CALCULATED → FINALIZED` with backend-enforced immutability, snapshot-based piece-rate earnings, and attendance aggregation.
- RBAC verified end-to-end by integration tests: anonymous 401, OWNER read / mutation 403, STAFF full mutations; full suite 291 passed.
- Frontend static checks clean; the Attendance/Payroll UI follows the proven vertical-slice pattern.
- The full 291-test suite provides the regression baseline for Phase 7.
