# Phase 2 Completion Report

## 1. Summary

Phase 2 (Authentication & Role-Based Access Control) is complete. The application now has real JWT authentication and a two-role authorization model, per the Phase 2 documentation and the reviewer-confirmed decision that **OWNER is view-only for business operations** while **STAFF is the operational role** (Phase 0 docs describe OWNER as full-access; this conflict was raised and the reviewer chose the Phase 2 brief model — see Known Issues #1).

Implemented:

- `User.role` field with exactly `OWNER` / `STAFF` choices (migration `0002_user_role`).
- Public login (`POST /api/v1/auth/login/`) issuing access + refresh tokens plus user info.
- Refresh (`POST /api/v1/auth/refresh/`), current user (`GET /api/v1/auth/me/`), and logout (`POST /api/v1/auth/logout/`) with server-side refresh-token blacklisting.
- Reusable DRF permission classes: `IsOwner`, `IsStaffRole`, `IsOwnerOrStaff`.
- `create_owner` management command for the initial OWNER account bootstrap.
- Frontend central auth state (`AuthProvider`/`useAuth`), real login, protected routes, centralized Bearer injection, single-flight access-token refresh with failed-refresh logout, token persistence (localStorage vs sessionStorage via "Remember Me"), logout flow, and role-aware navigation foundation.
- Fixed a latent Phase 1 bug: DRF 3.17 renamed `DEFAULT_EXCEPTION_HANDLER` → `EXCEPTION_HANDLER`, so the standardized error handler was never actually applied through real requests. It is now correctly wired and covered by a regression test.

## 2. User Model Changes

`apps/authentication/models.py`:

- Added `class Role(models.TextChoices)` with `OWNER = "OWNER"` and `STAFF = "STAFF"` — exactly two application roles.
- Added `User.role = CharField(max_length=10, choices=Role.choices, default=Role.STAFF)`.
- Migration `apps/authentication/migrations/0002_user_role.py` adds the field with default `STAFF` (existing users keep data; the dev DB had none). `0001_initial` untouched.
- Django superusers do **not** create a third role: `is_superuser`/`is_staff` remain Django flags for admin access; application authorization reads `User.role`, which is always `OWNER` or `STAFF` (tested).
- Admin updated to expose `role` in `list_display`, `list_filter`, `fieldsets`, and `add_fieldsets`.

## 3. Backend Authentication

Base path `/api/v1/auth/` (registered in `config/urls.py`).

- **POST `/login/`** — public (`permission_classes=[]`, `authentication_classes=[]`). `LoginSerializer` authenticates via Django and returns `{access, refresh, user:{id, username, role, is_active}}`. Invalid credentials raise `InvalidCredentials` (401, code `authentication_failed`) with an identical message for unknown usernames and wrong passwords so account existence is never revealed. No passwords/hashes are returned.
- **POST `/refresh/`** — SimpleJWT `TokenRefreshView` (public entry point requiring a valid refresh token). Returns `{access}`.
- **GET `/me/`** — `IsAuthenticated`. Returns `{id, username, role, is_active}` only.
- **POST `/logout/`** — `IsAuthenticated`. `LogoutSerializer` blacklists the supplied refresh token via SimpleJWT's token blacklist. Returns `{success: true, message: ...}`. Blacklisted refresh tokens cannot be reused at `/refresh/` (401 `token_not_valid`).
- `rest_framework_simplejwt.token_blacklist` added to `INSTALLED_APPS`; its migrations applied.

### Security / error handling

- Standardized error contract preserved: `{"success": false, "error": {"code", "message", "details?"}}`.
- Fixed DRF 3.17 setting rename (`EXCEPTION_HANDLER`), which made the Phase 1 handler apply only to direct calls, not real requests.
- `_extract_message` now recursively pulls readable text out of dict/list details (SimpleJWT wraps `InvalidToken` detail as a dict), so messages like `"Token is blacklisted"` are surfaced.
- Invalid login → 401 (not 403): handled via `apps/authentication/exceptions.py:InvalidCredentials`, a non-`AuthenticationFailed` 401 so DRF's `handle_exception` does not downgrade it to 403 on header-less public views.
- SimpleJWT config unchanged from Phase 1 (access 60 min, refresh 1 day, HS256, Bearer, no rotation).

## 4. Authorization / Roles

`apps/authentication/permissions.py`:

- `IsOwner` — `role == OWNER`.
- `IsStaffRole` — `role == STAFF` (operational role; unrelated to Django `is_staff`).
- `IsOwnerOrStaff` — any authenticated user with a valid application role (read/view operations).

All read `request.user.role` from the authenticated database user; a role supplied by the frontend is never trusted (tested by mutating a user's role in the DB after token issuance).

Application role `STAFF` is deliberately distinct from Django's `is_staff` flag (tested). OWNER is recognized as view-only: a mutation-style view behind `IsStaffRole` returns 403 for OWNER and 200 for STAFF (tested). No fake business CRUD was created; permission behavior is exercised through thin test-only views.

## 5. Frontend Authentication

- **`src/context/authContext.ts` / `AuthProvider.tsx` / `useAuth.ts`** — central auth state exposing `isAuthenticated`, `isLoading`, `user`, `role`, `login(credentials, remember?)`, `logout()`. On boot it restores the session via `/me/` when tokens exist.
- **`src/services/authToken.ts`** — centralized token service: access + refresh token storage; `localStorage` when "Remember Me" is checked, `sessionStorage` otherwise; `clearTokens()` clears both.
- **`src/services/authService.ts`** — `login`, `refresh`, `me`, `logout` API calls.
- **`src/services/apiClient.ts`** — request interceptor injects `Authorization: Bearer <access>`; response interceptor performs a single-flight refresh on `401` (auth endpoints excluded to avoid loops), retries the original request, and on refresh failure clears tokens and notifies the auth layer to log out.
- **`src/components/ProtectedRoute.tsx`** — renders a loading screen while auth bootstraps and redirects unauthenticated users to `/login`.
- **`src/routes/AppRoutes.tsx`** — protected routes wrapped in `ProtectedRoute`; `/login` is public.
- **`src/pages/Login.tsx`** — real login (mock navigation removed): validation, loading state, standardized error display (safe messages), show/hide password, "Remember Me" wiring, redirect after success.
- **`src/components/Header.tsx`** — real username + role chip + Sign Out wired to `logout()`.
- **`src/components/Sidebar.tsx` + `src/types/navigation.ts`** — role-aware navigation foundation: `NavItem.roles` filtering (UX only; all current placeholder items are visible to both roles).
- Logout clears local credentials even if the backend call fails (explicit user intent wins).

## 6. Security

- Passwords hashed by Django; never stored/logged/returned as plaintext or hashes (tested).
- Tokens never logged or rendered as raw HTML (no `dangerouslySetInnerHTML` added).
- Invalid login does not reveal account existence (identical 401 message — tested).
- CORS unchanged from Phase 1 (restricted to configured origins; not loosened).
- JWT configuration remains centralized in `settings.SIMPLE_JWT`.
- Backend authorization is authoritative; frontend role values are never trusted (tested).
- Cookie authentication not introduced; bearer JWT only.
- PostgreSQL-only configuration preserved; no SQLite.
- No secrets committed; `.env` ignored, `.env.example` committed (and extended for `OWNER_USERNAME`/`OWNER_PASSWORD` documentation).

## 7. Tests

Backend: **54 tests passing** (16 in `config`/`apps/common` including the new handler-wiring regression, 38 in `apps/authentication`).

- Roles: OWNER/STAFF assignable; invalid role rejected; exactly two roles; superuser is never a third role; `is_staff` independent of role.
- Login: OWNER and STAFF succeed; invalid credentials 401 with safe identical message; missing fields 400; inactive user rejected; no passwords/hashes in response.
- Tokens: access works; invalid access rejected; refresh produces a valid access token; invalid refresh rejected.
- Me: authenticated 200; anonymous 401; role returned; sensitive fields absent.
- Logout: succeeds; blacklisted refresh token cannot be reused; requires authentication; rejects invalid refresh body.
- Permissions: anonymous denied; OWNER recognized; STAFF recognized; OWNER denied on protected mutation (`IsStaffRole` → 403); STAFF authorized (200); shared read (`IsOwnerOrStaff`) accessible to both; DB role change takes effect (no frontend-role trust).
- `create_owner`: creates OWNER, optional superuser, promotes existing account, requires a password.

Frontend: static verification via `npm run lint`, `npx tsc --noEmit`, `npm run build` (all exit 0).

## 8. Verification Results

### Backend

```
Command:  python manage.py check
Result:   System check identified no issues (0 silenced).
Status:   PASS

Command:  python manage.py migrate --check
Result:   No missing migrations.
Status:   PASS

Command:  python -m pytest
Result:   54 passed in ~22s
Status:   PASS

Command:  black --check .
Result:   All done! 38 files would be left unchanged.
Status:   PASS

Command:  isort --check-only .
Result:   38 files would be left unchanged. Skipped 2 files.
Status:   PASS
```

### Frontend

```
Command:  npm run lint
Result:   Exit 0, no errors/warnings.
Status:   PASS

Command:  npx tsc --noEmit
Result:   Exit 0.
Status:   PASS

Command:  npm run build
Result:   Exit 0. Built in ~5.8s. Non-fatal chunk-size warning (737 kB) — deferred.
Status:   PASS
```

### Integration (backend :8000 + frontend dev server :5173, via Vite proxy)

```
Command:  POST http://127.0.0.1:5173/api/v1/auth/login/  {owner / Owner@12345}
Result:   200 {"access":..., "refresh":..., "user":{..., "role":"OWNER", "is_active":true}}
Status:   PASS

Command:  GET  http://127.0.0.1:5173/api/v1/auth/me/  (Bearer access)
Result:   200 {"id":1,"username":"owner","role":"OWNER","is_active":true}
Status:   PASS

Command:  POST http://127.0.0.1:5173/api/v1/auth/refresh/  {refresh}
Result:   200 {"access":"<new>"}
Status:   PASS

Command:  GET  http://127.0.0.1:5173/api/v1/auth/me/  (Bearer refreshed access)
Result:   200 username=owner role=OWNER
Status:   PASS

Command:  POST http://127.0.0.1:5173/api/v1/auth/logout/  {refresh} (Bearer access)
Result:   200 {"success":true}
Status:   PASS

Command:  POST http://127.0.0.1:5173/api/v1/auth/refresh/  (reuse logged-out refresh)
Result:   401 standardized error (refresh token blacklisted)
Status:   PASS

Command:  POST http://127.0.0.1:5173/api/v1/auth/login/  {staff / Staff@12345}
Result:   200 user.role = "STAFF"
Status:   PASS

Command:  POST http://127.0.0.1:5173/api/v1/auth/login/  {owner / wrong password}
Result:   401 standardized error, message identical to unknown-username case
Status:   PASS

Command:  GET http://127.0.0.1:5173/
Result:   200 (frontend SPA served)
Status:   PASS
```

### Manual (interactive-browser) verification

The interactive browser checks in `06_TESTING_AND_ACCEPTANCE.md` (visual login page, OWNER/STAFF login clicks, browser refresh behavior, protected-route redirect UX, role state in the header) could **not** be executed in this environment (no browser automation available). Their underlying flows were verified instead via the live integration harness above plus code/type/build review.

```
Command:  Manual browser walkthrough of 06_TESTING items 1-8
Result:   Not executed — no interactive browser available in this environment.
          Backend behaviors behind each item verified via integration harness.
Status:   BLOCKED (environment)
```

## 9. Commands Executed

```
python manage.py makemigrations authentication
python manage.py migrate
python manage.py shell  (create owner/staff dev users, API smoke tests)
python manage.py create_owner --username smoketest --password SmokePass123 --superuser
python manage.py check
python manage.py migrate --check
python -m pytest
black .
black --check .
isort .
isort --check-only .
npm run lint
npx tsc --noEmit
npm run build
# Integration: python manage.py runserver 0.0.0.0:8000 + npm run dev (5173)
# then PowerShell Invoke-RestMethod through the Vite proxy (login/me/refresh/logout/reuse)
```

## 10. Files Created/Modified

### Created (backend)

- `apps/authentication/exceptions.py`
- `apps/authentication/permissions.py`
- `apps/authentication/serializers.py`
- `apps/authentication/views.py`
- `apps/authentication/urls.py`
- `apps/authentication/migrations/0002_user_role.py`
- `apps/authentication/management/commands/create_owner.py`
- `apps/authentication/tests/{__init__.py, helpers.py, permission_urls.py, test_roles.py, test_login.py, test_tokens.py, test_me.py, test_logout.py, test_permissions.py, test_create_owner_command.py}`

### Modified (backend)

- `apps/authentication/models.py` — `Role` choices + `role` field
- `apps/authentication/admin.py` — role admin integration
- `config/settings.py` — `token_blacklist` app; `DEFAULT_EXCEPTION_HANDLER` → `EXCEPTION_HANDLER`
- `config/urls.py` — `/api/v1/auth/` routes
- `config/tests/test_settings.py` — updated setting key
- `apps/common/exceptions.py` — recursive `_extract_message`
- `apps/common/tests/test_error_handling.py` — handler-wiring regression test

### Created (frontend)

- `src/context/authContext.ts`, `src/context/AuthProvider.tsx`, `src/context/useAuth.ts`
- `src/components/ProtectedRoute.tsx`
- `src/services/authService.ts`

### Modified (frontend)

- `src/types/api.ts` — auth types (`UserRole`, `AuthUser`, `LoginResponse`, etc.)
- `src/services/authToken.ts` — access + refresh storage, remember-me storage choice
- `src/services/apiClient.ts` — refresh interceptor + `setOnAuthExpired`
- `src/pages/Login.tsx` — real login (mock removed)
- `src/components/Header.tsx` — real user/role + logout
- `src/components/Sidebar.tsx`, `src/types/navigation.ts` — role-aware nav foundation
- `src/routes/AppRoutes.tsx` — protected routes
- `src/App.tsx` — `AuthProvider` wiring

### Docs

- `README.md` — Authentication & Roles section, phase status
- `docs/PHASE_2_COMPLETION_REPORT.md` — this report

## 11. Known Issues

1. **OWNER role model conflict (Phase 0 vs Phase 2).** Phase 0 docs (`04_ROLES_PERMISSIONS.md`, validation report) describe OWNER as full-access / not view-only; the Phase 2 brief and `07_PHASE_2_ACCEPTANCE_CRITERIA.md` specify OWNER view-only for business. The reviewer explicitly chose **OWNER view-only for Phase 2**. This must be reconciled before the staff-administration phase (owner-only admin vs. view-only business reads).
2. **Latent Phase 1 bug fixed in Phase 2.** DRF 3.17 renamed `DEFAULT_EXCEPTION_HANDLER` → `EXCEPTION_HANDLER`; the Phase 1 handler was silently bypassed by real requests (Phase 1 tests only called the handler directly). Fixed and covered by a request-level regression test.
3. **react-router npm advisory (high, from Phase 1).** `react-router-dom@7.18.x` in the vulnerable range of `GHSA-qwww-vcr4-c8h2` (RSC-mode CSRF bypass); app uses client-side `BrowserRouter` only. Upgrade when a fixed release exists.
4. **Vite chunk-size warning (737 kB).** Non-fatal; code-splitting deferred until business pages exist.
5. **Custom 404/500 JSON handlers active only when `DEBUG=False`** (Phase 1 note, unchanged).
6. **Logout with an already-expired/invalid access token** still clears local credentials (backend call fails but local logout proceeds) — intended behavior.
7. **`docs/PHASE_1_COMPLETION_REPORT.md` git deletion is uncommitted** (the file moved to `docs/phase-1/` in Phase 1). Left for the reviewer/commit step.

## 12. Deferred Items

- Business APIs and their authorization mapping (`IsStaffRole` for mutations, `IsOwnerOrStaff` for reads) — Phases 3+.
- Staff account administration (owner-only) and `is_staff`/admin access policy — later phase.
- Rate limiting — explicitly not built in this phase per `05_SECURITY_AND_SESSION_RULES.md` (documented only).
- Access-token revocation at logout — only the refresh token is blacklisted (standard SimpleJWT behavior; access tokens remain valid until expiry).
- Frontend automated tests — no frontend test runner exists in the Phase 1 foundation; verification is static checks + live integration.
- Interactive-browser manual verification of the login UI — not executable in this environment (see §8).
- Forgot-password flow — remains a placeholder link (out of Phase 2 scope).

## 13. Phase 3 Readiness

Ready. Phase 3 can build business APIs on top of:

- Real JWT auth with `/login`, `/refresh`, `/me`, `/logout`.
- Reusable backend permissions (`IsOwner`, `IsStaffRole`, `IsOwnerOrStaff`) to enforce the business matrix.
- SimpleJWT blacklist configured and tested for logout invalidation.
- Centralized frontend auth state, protected routes, single-flight refresh, and role-aware navigation.
- `create_owner` bootstrap command and documented local-dev auth setup.
- PostgreSQL-only, versioned API, standardized errors, logging, pagination, and health check all intact.
