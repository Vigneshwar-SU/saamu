# Settings Completion Report

## Status
**Implementation:** PASS
**Manual verification:** PENDING

## Implemented
### Reused Functionality (no new sources of truth)
- The Settings UI is backed entirely by the existing database-backed `ShopDetails` singleton (`apps/billing/models.py`, created with the established defaults on first access and already used for the shop block on the digital bill). No shop data is hard-coded in the frontend and no duplicate model/endpoint was introduced.
- Current-account information is shown from the authenticated `/auth/me` user already loaded by the frontend auth context (`useAuth().user`) — the same server-authoritative source as login.
- Backend authorization reuses the existing `IsOwnerOrStaff` / `IsStaffRole` permission classes and follows the project-wide convention: **OWNER is view-only, STAFF manages**. This matches billing, orders and salary-configuration behaviour.
- The digital bill (`GET /api/v1/invoices/<id>/bill/`) already reads shop details at request time, so saved settings flow to the bill automatically — no rebuild required.

### Backend
- Added `ShopDetailsSerializer` (`apps/billing/serializers.py`): read/update representation exposing only the supported shop identity fields (`name`, `tagline`, `address`, `phone`, `established_year` plus read-only `id`). Server-side validation mirrors the model constraints and rejects empty names and implausible establishment years (must be 1000–2100), so the bill's shop block can never be blank or nonsensical. No sensitive/secret fields exist on the model or are exposed.
- Added `ShopDetailsView` (`apps/billing/views.py`):
  - `GET /api/v1/settings/shop-details/` — OWNER or STAFF.
  - `PUT /api/v1/settings/shop-details/` — STAFF only (OWNER receives 403; authorization is server-authoritative).
  - Both operations resolve the singleton via `ShopDetails.shop_details()`, so updates always target the single authoritative row.
- Registered the route in `apps/billing/urls.py`.
- Added `apps/billing/tests/test_settings.py` (8 tests): anonymous denied (401), OWNER read (200, exact field set), OWNER cannot update (403, row unchanged), STAFF update persists (200 + model check), singleton stays single-row, updated details flow into the digital bill, and 400 validation for blank name and implausible year.

### Frontend
- Replaced the `/settings` placeholder with a real `Settings` page (`frontend/src/pages/Settings.tsx`):
  - **Shop Details** form backed by `useShopDetails()` (React Query, `GET /settings/shop-details/`) with react-hook-form + zod validation matching the backend rules (name required ≤100, tagline ≤200, phone ≤30, address ≤2000, established year integer 1000–2100).
  - Loading spinner, API-error state with Retry, inline success alert after save, inline error alert on failure; success clears as soon as the user edits the form.
  - STAFF can edit and Save (Save disabled until the form is dirty; saving shows a spinner). OWNER sees the read-only form plus an informational alert explaining view-only access.
  - **Current Account** read-only card (username, role, active status) from the authenticated user.
- Added `types/settings.ts` (`ShopDetails`, `ShopDetailsPayload`) so the API contract is type-safe.
- Added `services/settingsService.ts` (`getShopDetails`, `updateShopDetails`).
- Added `hooks/useSettings.ts`: `useShopDetails` query and `useUpdateShopDetails` mutation that seeds the query cache and invalidates the `invoice-bill` cache on success so an open digital bill re-renders the updated shop block (`INVOICE_BILL_KEY` exported from `useInvoices.ts`).
- Updated `AppRoutes.tsx` to import `Settings` from `pages/Settings`; deleted the now-unused `pages/Placeholders.tsx`.

### Integration
- Settings saved through the page update the single `ShopDetails` row, which the digital bill endpoint reads at request time — the printed bill and customer communications show the authoritative profile with no client-side duplication.
- Mutation invalidates the React Query `invoice-bill` caches, keeping any open bill view in sync.

## API Changes
- New endpoint `GET /api/v1/settings/shop-details/` (OWNER or STAFF) → 200 with the shop profile.
- New endpoint `PUT /api/v1/settings/shop-details/` (STAFF only) → 200 with the saved profile, 403 for OWNER, 400 with `error.details` for invalid payloads, 401 anonymous.
- No existing endpoint was modified or removed.

## RBAC Behavior
- OWNER: view-only — can read shop details (GET) but any update attempt returns 403; the UI shows the disabled form.
- STAFF: can read and update shop details (GET/PUT).
- Authorization is enforced server-side via `IsStaffRole`/`IsOwnerOrStaff`; the frontend role check is presentation-only.

## Files Changed
- `backend/apps/billing/serializers.py`
- `backend/apps/billing/views.py`
- `backend/apps/billing/urls.py`
- `backend/apps/billing/tests/test_settings.py` (new)
- `frontend/src/types/settings.ts` (new)
- `frontend/src/services/settingsService.ts` (new)
- `frontend/src/hooks/useSettings.ts` (new)
- `frontend/src/hooks/useInvoices.ts` (exported `INVOICE_BILL_KEY`)
- `frontend/src/pages/Settings.tsx` (new)
- `frontend/src/routes/AppRoutes.tsx`
- `frontend/src/pages/Placeholders.tsx` (deleted)

## Migrations
- None. `python manage.py makemigrations --check --dry-run` reports no changes; `python manage.py migrate --plan` shows no planned operations.

## Automated Verification
| Check | Result |
|---|---|
| Django check | PASS — `manage.py check` reports no issues |
| Migration check | PASS — no changes detected |
| Backend tests | PASS — full suite 774 tests passed (766 prior + 8 new settings tests) |
| TypeScript | PASS — `tsc` clean |
| ESLint | PASS — `npm run lint` clean (max-warnings 0) |
| Frontend build | PASS — `vite build` succeeded (pre-existing chunk-size warning only) |

## Known Issues
- The account card shows only the fields the API exposes for the authenticated user (username, role, active status); there is deliberately no email/phone/name in `UserSerializer` (secret-free design), so richer profile fields are out of scope.
- Shop identity is the supported preference set today (name, tagline, address, phone, established year); no speculative preferences (e.g. dark mode, notifications) were added because no authoritative backend support exists for them.
- Vite reports a single large-chunk warning (`index-*.js > 500 kB`) which predates this task and is unrelated to the Settings module.

## Manual Verification
Not performed yet. The project owner will perform comprehensive manual verification later.
