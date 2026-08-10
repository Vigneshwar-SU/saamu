# Password Reset — Completion Report

## Status

| Item | Status |
| --- | --- |
| Implementation | DONE |
| Automated tests | PASS (800/800 backend) |
| Frontend lint / tsc / build | PASS |
| Manual verification (real Gmail) | **PENDING** |
| Real email delivery test | **PENDING** |

Manual verification must be performed by the project owner before this phase is
considered fully complete. See `07-manual-verification.md`.

## Objective

Replace the Forgot Password placeholder with a complete, secure, email-based
password reset flow for OWNER and STAFF accounts, using real Gmail SMTP
delivery configured purely through environment variables.

## API endpoints

- `POST /api/v1/auth/password-reset/` — request a reset link.
  Body: `{ "email": "..." }`. Always returns the generic success message.
- `POST /api/v1/auth/password-reset/confirm/` — apply a new password.
  Body: `{ "uid", "token", "new_password", "confirm_password" }`.

Both are public (no JWT) and rate-limited via DRF `ScopedRateThrottle`
(`password_reset_request` = 5/hour, `password_reset_confirm` = 30/hour,
overridable by env).

## Backend changes

- `apps/authentication/password_reset.py` (new): token service using Django's
  `PasswordResetTokenGenerator`; SHA-256 digest persistence; single-use
  enforcement; generic no-enumeration messaging; branded email via
  `EmailMultiAlternatives` (HTML + plain text).
- `apps/authentication/models.py`: new `PasswordResetToken` model (`user`,
  `token_hash`, `used`, `used_at`; indexes on `(user, used)` and `token_hash`).
- `apps/authentication/views.py`: `PasswordResetRequestView` and
  `PasswordResetConfirmView` (public, rate-limited, generic responses).
- `apps/authentication/serializers.py`: `PasswordResetRequestSerializer`
  (email) and `PasswordResetConfirmSerializer` (uid/token/new/confirm with
  mismatch error on `confirm_password`).
- `apps/authentication/urls.py`: reset routes wired.
- `apps/authentication/exceptions.py`: `PasswordResetTokenInvalid`
  (`invalid_reset_token`, 400).
- `apps/authentication/templates/authentication/password_reset_email.{html,txt}`:
  branded reset email with button, URL fallback, expiry and ignore-warning.
- `apps/authentication/tests/test_password_reset.py` (new): 26 tests.
- `config/settings.py`: env-driven `EMAIL_*`, `DEFAULT_FROM_EMAIL`,
  `FRONTEND_URL`, `PASSWORD_RESET_TIMEOUT`, and `DEFAULT_THROTTLE_RATES` inside
  `REST_FRAMEWORK`.
- `config/configuration_validation.py`: production validation now also requires
  email settings and a non-loopback `FRONTEND_URL`.
- `apps/authentication/migrations/0003_passwordresettoken.py` (new).

## Frontend changes

- `pages/ForgotPassword.tsx` (new): email form, generic success state,
  loading state.
- `pages/ResetPassword.tsx` (new): new + confirm password with visibility
  toggles; success, invalid-link and inline-error states; **Request New Link**.
- `services/authService.ts`: `requestPasswordReset`, `confirmPasswordReset`
  (reusing the existing `apiClient`).
- `hooks/usePasswordReset.ts` (new): `useRequestPasswordReset`,
  `useConfirmPasswordReset`.
- `types/api.ts`: `MessageResponse`, `PasswordResetConfirmPayload`.
- `routes/AppRoutes.tsx`: `/forgot-password` and `/reset-password/:uid/:token`.
- `pages/Login.tsx`: Forgot Password? now navigates to `/forgot-password`.

## Email configuration

Gmail SMTP via environment variables (`EMAIL_HOST=smtp.gmail.com`,
`EMAIL_PORT=587`, `EMAIL_USE_TLS=True`, `EMAIL_HOST_USER=saamutailors1954@gmail.com`,
`EMAIL_HOST_PASSWORD=<App Password>`). Reset link built from `FRONTEND_URL`
(`http://localhost:5173/reset-password/<uid>/<token>`), lifetime
`PASSWORD_RESET_TIMEOUT=900` (15 min). `.env.example` has placeholders only;
`.env` is git-ignored; no credentials committed.

## Security considerations

- No account enumeration (identical generic response; inactive/unknown get no
  email).
- Raw tokens never stored — only SHA-256 digests; single-use + time-limited;
  invalidated automatically on password change.
- Backend password validators authoritative; token not consumed on weak
  password attempts.
- No auto-login after reset; role/username/status unchanged; JWT flow and
  existing auth untouched.

## Files changed

Backend: `apps/authentication/{password_reset,models,views,serializers,urls,exceptions}.py`,
`apps/authentication/tests/test_password_reset.py`,
`apps/authentication/migrations/0003_passwordresettoken.py`,
`apps/authentication/templates/authentication/password_reset_email.{html,txt}`,
`config/settings.py`, `config/configuration_validation.py`,
`config/tests/test_configuration_validation.py`,
`config/tests/test_security_hardening.py`, `.env`, `.env.example`, `.gitignore`.

Frontend: `pages/{Login,ForgotPassword,ResetPassword}.tsx`,
`services/authService.ts`, `hooks/usePasswordReset.ts`, `types/api.ts`,
`routes/AppRoutes.tsx`.

Docs: `docs/password_reset/01-overview.md` … `07-manual-verification.md`,
`COMPLETION_REPORT.md`.

## Migration status

`authentication.0003_passwordresettoken` — created, `migrate --plan` lists it,
`makemigrations --check --dry-run` reports no pending changes.

## Automated test results

- `manage.py check` — no issues.
- `manage.py makemigrations --check --dry-run` — no changes.
- `manage.py migrate --plan` — only `authentication.0003_passwordresettoken`.
- `pytest` — **800 passed** (774 pre-existing + 26 new password-reset tests).
- `npm run lint` — clean.
- `npx tsc --noEmit` — passes.
- `npm run build` — passes (pre-existing chunk-size warning only).

## Known issues

- None known. The pre-existing Vite chunk-size warning is unrelated to this
  phase.
- Emails are not globally unique in the user model; reset links are still
  unambiguous because the user id is encoded in the uid and bound into the
  token digest (documented in `05-security.md`).

## Manual verification status

**PENDING** — real Gmail delivery and the end-to-end flow (see
`07-manual-verification.md`) have not yet been performed by the project owner.
