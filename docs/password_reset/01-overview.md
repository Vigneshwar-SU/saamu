# Password Reset — Overview

Phase: Email-Based Password Reset
Implementation: DONE
Manual Verification: PENDING

## Objective

Replace the placeholder Forgot Password behaviour with a complete, secure,
real-world email-based password reset flow for Saamu Tailors. The feature works
for both **OWNER** and **STAFF** accounts using a single account-based
mechanism - there is no role-specific reset implementation.

The shop email `saamutailors1954@gmail.com` is used as the operational sender
during this phase, configured through environment variables (Gmail SMTP with an
App Password) so no credentials are ever committed.

## Workflow

1. Login page → **Forgot Password?**
2. User enters the registered email address.
3. Backend checks the account without revealing whether it exists.
4. A secure, time-limited reset email is sent (only to existing active accounts).
5. The email contains a reset link `FRONTEND_URL/reset-password/<uid>/<token>`.
6. The user opens the link on the Reset Password page, enters and confirms a
   new password.
7. Backend validates the token and the password, then changes the password.
8. The token becomes unusable; the user returns to Login and signs in with the
   new password. The system does **not** auto-log the user in.

## Design Principles

- **No account enumeration.** The request endpoint always returns the same
  generic success message whether or not the email exists.
- **No plain-text tokens.** The raw token is emailed and only its SHA-256 digest
  is stored; the token is single-use and expires after `PASSWORD_RESET_TIMEOUT`.
- **Django's proven token generator.** `PasswordResetTokenGenerator` is reused
  rather than building a custom token system.
- **Backend authoritative.** All password validation happens on the backend;
  frontend validation is convenience only.
- **No redesign.** The existing authentication system, JWT flow, RBAC and Login
  page are untouched apart from the Forgot Password link.

## Key Files

- Backend: `backend/apps/authentication/password_reset.py`,
  `backend/apps/authentication/{models,views,serializers,urls,exceptions}.py`,
  `backend/apps/authentication/tests/test_password_reset.py`
- Frontend: `frontend/src/pages/{ForgotPassword,ResetPassword}.tsx`,
  `frontend/src/services/authService.ts`, `frontend/src/hooks/usePasswordReset.ts`,
  `frontend/src/routes/AppRoutes.tsx`, `frontend/src/pages/Login.tsx`
- Config: `backend/config/settings.py`, `backend/config/configuration_validation.py`,
  `backend/.env`, `backend/.env.example`

See the companion documents:

- [02-backend.md](./02-backend.md)
- [03-frontend.md](./03-frontend.md)
- [04-email-configuration.md](./04-email-configuration.md)
- [05-security.md](./05-security.md)
- [06-testing.md](./06-testing.md)
- [07-manual-verification.md](./07-manual-verification.md)
- [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)
