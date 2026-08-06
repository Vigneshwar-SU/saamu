# Phase 19 Completion Report

## 1. Status
**PASS** — automated verification complete. Manual verification is **NOT STARTED** (no human has executed `docs/phase-19/08_PHASE_19_MANUAL_VERIFICATION.md`).

## 2. Scope
Phase 19 is a **preparation/review reminder workflow** built on the Phase 18 WhatsApp-ready foundation. It derives eligible reminders from existing authoritative order/payment/customer state, prepares each message deterministically via the Phase 18 communication layer, and exposes an operator review surface (list + per-reminder prepare) for Copy WhatsApp Message / Open WhatsApp handoff. **No automatic external sending of any kind** (no WhatsApp/SMS/email senders, no Meta/Twilio/provider SDKs, no webhooks, no credentials, no background tasks). Reminders are **derived, never stored** — there is no new table and no migration, and repeated reads are idempotent.

## 3. Implementation Summary
- Two reminder types, justified strictly by data that already exists:
  - `READY_FOR_COLLECTION` — an active order whose status is `READY`; prepared with the Phase 18 `MESSAGE_TYPE_READY_FOR_COLLECTION` template.
  - `BALANCE_OUTSTANDING` — an active order that has an invoice (`order_payment_summary()` → `has_invoice`) with `outstanding_balance > 0`; prepared with the Phase 18 `MESSAGE_TYPE_PAYMENT_BALANCE` template.
- **No invoice → never a balance reminder** (there is no billable relationship yet, so a payment reminder would be premature). **Terminal orders** (`COLLECTED` / `CANCELLED`) are excluded from both reminder types.
- Every message is authored by the existing Phase 18 `build_order_communication`, so wording, INR formatting, phone normalization and the `wa.me` URL agree exactly with the Order Detail communication panel. The only phone source is the existing `Customer.mobile_number`.
- Deterministic candidate ordering: orders ascending by `id`, then the fixed `REMINDER_TYPES` order. Nothing is persisted, so nothing can be duplicated — the idempotency guarantee.
- Stale-safe handoff: `prepare` re-evaluates eligibility against current state and returns a clear 400 `validation_error` with a stable `REASON_*` code (`ORDER_TERMINAL`, `ORDER_NOT_READY`, `NO_INVOICE`, `NO_OUTSTANDING_BALANCE`) when the reminder can no longer be prepared.
- Frontend: a `Reminders` page (sidebar entry, `/reminders`) renders server-derived candidates with a Type label, order status chip, customer, order number, server-authored message preview, and Copy / Open WhatsApp actions. It never calculates balances or eligibility. Loading/empty/error/retry, pagination, refresh, disabled Open state with explanation when no usable number, and per-card duplicate-action protection are implemented.

## 4. Backend Changes
- **New `backend/apps/billing/reminders.py`** — the Phase 19 orchestration layer:
  - `REMINDER_TYPES`, `REMINDER_TYPE_LABELS`, `REMINDER_MESSAGE_TYPES` (mapping to the Phase 18 `MESSAGE_TYPE_*` constants), stable `REASON_*` codes.
  - `reminder_id()` / `parse_reminder_id()` — stable id `<TYPE>_<order_id>`; parsed with `rpartition("_")` so type names that contain underscores are handled correctly.
  - `ReminderNotEligible(code, message)` exception.
  - `evaluate_reminder_eligibility(order, type)` — pure, deterministic; raises `ValueError` for unsupported types.
  - `build_reminder_candidate(order, type)` — re-validates eligibility, prepares via Phase 18, returns the full candidate payload.
  - `build_pending_reminders()` — active orders only (`exclude(status__in=TERMINAL_STATUSES)`), `select_related("customer")`, ordered by `id` then `REMINDER_TYPES`.
- **Modified `backend/apps/billing/views.py`**:
  - `ReminderListAPIView` — GET-only, `IsOwnerOrStaff`, `PageNumberPagination` (20/page), `{success, data: {count, next, previous, results}}` envelope.
  - `ReminderPrepareAPIView` — GET-only, `IsOwnerOrStaff`; 400 `validation_error` for invalid reminder id and for stale reminders (`ReminderNotEligible` → `{reminder_id: "<reason> (<code>)."}`); 404 for a missing order.
- **Modified `backend/apps/billing/urls.py`** — routes `communications/reminders/` and `communications/reminders/<str:reminder_id>/prepare/`.

## 5. Frontend Changes
- **New `frontend/src/types/reminders.ts`** — `ReminderType`, `REMINDER_TYPES`, `REMINDER_TYPE_LABELS`, `ReminderCandidate`, `ReminderListData`, `ReminderListResponse`, `ReminderPrepareResponse`.
- **New `frontend/src/services/remindersService.ts`** — `listReminders(page)`, `prepareReminder(id)` via the shared `apiClient`.
- **New `frontend/src/hooks/useReminders.ts`** — TanStack Query `useReminderList(page)` keyed on page.
- **New `frontend/src/hooks/useReminderActions.ts`** — per-card copy (2-second copied state, reuses `copyToClipboard`) and open (re-fetches the prepared reminder at handoff time, opens the server-provided `whatsapp_url` only, duplicate-action protected, recoverable error display, timer cleanup on unmount).
- **New `frontend/src/pages/Reminders.tsx`** — review surface with breadcrumbs, header, refresh, loading/error/retry/empty states, pagination, and per-card actions; no client-side balance/eligibility calculation.
- **Modified `frontend/src/routes/AppRoutes.tsx`** — `/reminders` route inside the authenticated layout.
- **Modified `frontend/src/constants/navigation.ts`** — `Reminders` sidebar entry with `NotificationsActiveIcon`.

## 6. Database Changes
**None.** No models, no fields, no migrations. Reminders are derived on every read from existing order/payment/customer state. `makemigrations --check --dry-run` → "No changes detected".

## 7. API Changes
- `GET /api/v1/communications/reminders/` — paginated list of currently eligible reminder candidates. 401 anonymous; 403 non-owner/staff; 405 non-GET.
- `GET /api/v1/communications/reminders/<TYPE>_<order_id>/prepare/` — re-validates eligibility and returns the prepared candidate `{id, reminder_type, reminder_type_label, order, customer, eligibility, message, phone_number, whatsapp_url}`. 400 `validation_error` (invalid id or stale reminder with stable `REASON_*` code); 404 missing order; 401/403/405 as above.
- Both are GET-only and read-only; nothing is created, mutated or sent. The existing standard `{success:false, error:{code, message, details?}}` error contract is preserved.

## 8. RBAC, Security & Privacy
- Both endpoints require `IsOwnerOrStaff` (OWNER and STAFF read-only); anonymous → 401.
- `Customer.mobile_number` remains the only phone source, normalized by the Phase 18 logic; a full phone number and `whatsapp_url` appear only in the prepared payload and are never logged.
- Messages contain only customer/order/payment facts; internal order notes are excluded (test `test_messages_exclude_internal_notes`).
- No mutation endpoints, no new permissions, no provider credentials.

## 9. Reminder Correctness
- **Eligibility** is a pure function of persisted state (`evaluate_reminder_eligibility`); tests cover both types, terminal exclusion, the no-invoice case, the zero-balance case and the ready-not-ready case.
- **Deterministic behavior**: candidate list ordered by order `id` then fixed `REMINDER_TYPES` order; both the builder and the list/prepare API are asserted to be repeatable (`test_pending_reminders_are_deterministic_and_ordered`, `test_list_is_deterministic`, `test_prepare_is_deterministic`).
- **Duplicate prevention**: nothing is persisted, so no reminder can be recorded twice; idempotency is structural, not bookkeeping. `test_reminders_never_mutate_business_records` proves order/payment counts, totals and statuses are unchanged by list and prepare.
- **Source-of-truth reuse**: messages come from the Phase 18 `build_order_communication` and financial figures from `order_payment_summary` (`test_pending_reminders_message_agrees_with_phase_18`, `test_balance_candidate_agrees_with_authoritative_summary`).

## 10. Testing Results
- Focused: `python -m pytest apps/billing/tests/test_reminders.py` — **50 tests passed** (37 test functions, parametrized cases expand the count).
- Full suite: `python -m pytest` — **702 passed** (~306s). Baseline before Phase 19 was 652 passed; the +50 delta matches the new Phase 19 tests.
- Backend gates: `python manage.py check` — no issues; `makemigrations --check --dry-run` — no changes detected; `black --check` and `isort --check-only` on the four Phase 19 Python files — clean.
- Frontend gates: `npm run lint` (0 errors), `npx tsc --noEmit` (clean), `npm run build` (success; only the pre-existing >500 kB chunk-size warning, unchanged by Phase 19).

## 11. Manual Verification
**NOT STARTED.** `docs/phase-19/08_PHASE_19_MANUAL_VERIFICATION.md` remains unchecked; automated tests do not count as manual verification.

## 12. Documentation
- `README.md` — Current stage line set to Phase 19; new section `## 8.8 Reminder Review & WhatsApp-Ready Preparation (Phase 19)`; billing app repository-layout line updated; phase-status list updated (`Phase 19 — complete`, `Phase 20+ — pending`).
- The existing Phase 19 planning documents (`01`–`13`) were read and used as the specification.

## 13. Files Changed
**Phase 19 — new:**
- `backend/apps/billing/reminders.py`
- `backend/apps/billing/tests/test_reminders.py`
- `frontend/src/types/reminders.ts`
- `frontend/src/services/remindersService.ts`
- `frontend/src/hooks/useReminders.ts`
- `frontend/src/hooks/useReminderActions.ts`
- `frontend/src/pages/Reminders.tsx`

**Phase 19 — modified:**
- `backend/apps/billing/views.py`
- `backend/apps/billing/urls.py`
- `frontend/src/routes/AppRoutes.tsx`
- `frontend/src/constants/navigation.ts`
- `README.md`

**Pre-existing work — untouched:** the working tree contained no uncommitted Phase 17/18 work when Phase 19 started (Phases 17 and 18 were committed as `13b6c28`). `git status` shows only the Phase 19 file set above.

## 14. Known Issues
- Frontend production build reports a pre-existing >500 kB chunk-size warning; not introduced by Phase 19 and not an error.

## 15. Deferred Items
- Automatic sending and all provider integrations (WhatsApp Business / Meta Cloud / Twilio / SMS / email), message history, webhooks, background senders/reminder scheduling, and customer-opt-out/delivery-status tracking — deferred to Phase 20+, consistent with the Phase 19 and Phase 18 specs.
- Any additional reminder types (e.g., order progress nudges for non-READY statuses) — deliberately out of scope; the two implemented types are the only ones justifiable from existing data.

## 16. Git Verification
No commit was created — the user has not requested one. `git status` confirms the working tree contains only the Phase 19 additions/modifications listed in section 13; HEAD remains `13b6c28` (Phase 18 + Phase 19 documentation/frontend groundwork). Nothing Phase 19-related has been committed.

## 17. Phase 20 Readiness
Ready. Phase 19 leaves the reminder workflow with deterministic, tested derivation and preparation, a stale-safe handoff, no new persistence, and no new security surface beyond two read-only OWNER/STAFF endpoints. Phase 20 can proceed with the deferred items in section 15 (automatic sending, scheduling, provider integration, message history) as the natural entry points, or with other business modules (e.g., cloud migration) as prioritized.
