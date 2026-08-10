# OWNER/STAFF Account Type Selector — Completion Report

## Implementation status

| Item | Status |
| --- | --- |
| Implementation | DONE |
| Backend automated tests | PASS (800/800) |
| Frontend lint / tsc / build | PASS |
| Manual verification | **PENDING** |

This phase adds a required **Account Type** selector (Owner → `OWNER`, Staff →
`STAFF`) to the Login and Forgot Password screens. The selector is a
**UX/testing aid only**: the backend user role (from the authenticated
database user and the issued JWT) remains authoritative. It is not trusted for
authorization and is never used to grant access. The Reset Password flow is
unchanged and intentionally has no role selector.

## Files changed

Frontend:

- `frontend/src/pages/Login.tsx` — required Account Type dropdown (above
  Username), role-match verification against the authenticated user.
- `frontend/src/pages/ForgotPassword.tsx` — required Account Type dropdown
  (above Email), client-side UX aid only.
- `frontend/src/context/AuthProvider.tsx` — `login()` now accepts an optional
  expected role and rejects the session on mismatch (before any token is
  stored).
- `frontend/src/context/authContext.ts` — `login` signature extended with
  `expectedRole?: UserRole`.

Backend: **none.**

API: **none.** Both `/api/v1/auth/login/` (body `{ username, password }`) and
`/api/v1/auth/password-reset/` (body `{ email }`) contracts are unchanged; the
Account Type is never sent to the backend.

## Frontend changes

### Login

- New `accountType` field on the Zod schema: `z.enum(USER_ROLES)` with
  `required_error` and default `OWNER`. `USER_ROLES`/`UserRole` are reused from
  `frontend/src/types/api.ts` (no new role state created).
- MUI `FormControl` + `InputLabel` + `Select` + `MenuItem` renders the dropdown
  above Username, matching the existing outlined field styling, spacing and
  `react-hook-form`/`zodResolver`/`Controller` patterns used across the app.
- On submit the selected Account Type is passed to `login()` as the expected
  role. `AuthProvider.login` calls `authService.login` first, then compares the
  **backend-provided** `user.role` against the selection:
  - Match → tokens are stored and the session is established (unchanged path).
  - Mismatch → `Error("Selected account type does not match this account.")`
    is thrown, **no token is stored and no user state is set**, so the login
    session is rejected and the exact message is rendered in the existing
    error `Alert` via `getApiErrorMessage`.
- Because the authoritative role comes from the `/auth/login/` response
  (JWT + user payload), selecting OWNER can never grant OWNER access to a
  STAFF account. Credential checks, loading, password visibility, remember-me,
  branding, validation and the authenticated-redirect effect are all preserved.
- A STAFF user selecting OWNER (or an OWNER user selecting STAFF) is rejected
  with the mismatch message — even if the same email is currently assigned to
  both roles during development, because the check uses the username + password
  identity the credentials resolve to, never the email.

### Forgot Password

- Same required Account Type dropdown (`z.enum(USER_ROLES)`, default `OWNER`),
  rendered above the Email field with identical styling.
- The selection is a UX/testing aid only and is **not** sent to the backend;
  the request stays `{ email }`, so no backend change was required.
- All existing behaviour is preserved: email validation, loading/success/error
  states, generic no-enumeration success message, rate limiting, and the Gmail
  reset flow. The response is identical for OWNER, STAFF, inactive and
  nonexistent emails — the selector never reveals or filters by role.

### Reset Password

- Unchanged. No role selector. The `/reset-password/:uid/:token` flow keeps the
  reset token/user identity authoritative and never trusts a client-provided
  role.

## Backend changes

None. No backend code, settings, migrations or Gmail SMTP configuration were
modified.

## API changes

None. The login and password-reset request/response contracts are unchanged.
The Account Type is not transmitted, so it cannot be used to influence backend
behavior.

## RBAC/security considerations

- No new role state: the existing `AuthUser.role` / `User.role` (OWNER/STAFF)
  remains the single source of truth.
- The OWNER/STAFF permission architecture is untouched
  (`apps/authentication/permissions.py`: `IsOwner`, `IsStaffRole`,
  `IsOwnerOrStaff`); backend authorization is not weakened.
- The dropdown is never trusted for authorization. OWNER access is only ever
  granted by a successful backend login whose authoritative `user.role` is
  OWNER.
- JWT behavior is preserved: tokens are issued/validated exactly as before, and
  a mismatch means no token is created at all.
- Password-reset security is fully preserved: single-use tokens, expiry,
  generic no-enumeration messaging, no automatic login after reset, and
  automatic invalidation after a password change (all in the untouched
  `apps/authentication/password_reset.py`).

## Automated verification results

- `python manage.py check` — no issues.
- `python manage.py makemigrations --check --dry-run` — "No changes detected".
- `python manage.py migrate --plan` — "No planned migration operations".
- `pytest` — **800 passed** (no failures; no new backend tests needed because
  no backend/API behavior changed).
- `npm run lint` — clean.
- `npx tsc --noEmit` — passes.
- `npm run build` — passes (pre-existing Vite chunk-size warning only, unrelated
  to this change).

## Known issues

- None introduced by this phase. The pre-existing Vite chunk-size warning and
  the existing non-unique-email model behavior are unrelated to this change.
- The Account Type dropdown for Forgot Password does not pre-filter or hint at
  the account's role by design (anti-enumeration); the same email shared by an
  OWNER and STAFF account still resolves by email, and the reset link's
  uid/token remain authoritative.

## Manual verification status

**PENDING** — to be performed by the project owner:

- Login as OWNER with Account Type = Owner → success.
- Login as STAFF with Account Type = Staff → success.
- Login as OWNER with Account Type = Staff (and vice versa) → rejected with
  "Selected account type does not match this account." and no session created.
- Forgot Password with Account Type = Owner and with Account Type = Staff →
  both complete the Gmail reset flow, and the account's role is unchanged after
  reset.
- Reset Password (no selector) → `/reset-password/:uid/:token` unchanged.
