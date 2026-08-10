# Password Reset — Frontend

## Routes

- `/login` — existing page; the **Forgot Password?** link now navigates to
  `/forgot-password` instead of showing a placeholder alert.
- `/forgot-password` — `ForgotPassword.tsx` (public).
- `/reset-password/:uid/:token` — `ResetPassword.tsx` (public).

## ForgotPassword page

- Single **Email Address** field (RHF + zod, `z.string().email(...)`).
- **Send Reset Link** button with a **Sending...** loading state; disabled while
  the request is in flight.
- On success it shows a generic success panel ("If an account exists with this
  email address, a password reset link has been sent. ... The link is valid for
  15 minutes.") — the same message regardless of whether the account exists, so
  the UI never reveals account existence.
- **Back to Sign In** link and button.

## ResetPassword page

- Reads `uid` and `token` from the route params.
- **New Password** and **Confirm New Password** fields, each with a visibility
  toggle (`Visibility` / `VisibilityOff` icons, matching Login).
- Client-side zod validation mirrors the backend: minimum 8 characters,
  not entirely numeric, and match confirmation. The backend remains
  authoritative.
- **Reset Password** button with a **Resetting Password...** loading state,
  disabled during submission.
- States:
  - **Success**: "Password Reset Successful" panel with a **Back to Sign In**
    button. The user is never auto-logged-in.
  - **Invalid / expired link** (backend `invalid_reset_token` or missing uid/
    token): dedicated "Reset Link Invalid" panel with a **Request New Link**
    button (→ `/forgot-password`) and a **Back to Sign In** link.
  - **Other errors** (network, weak password): inline red alert showing the
    backend message.

## Service & hooks

- `authService.requestPasswordReset(email)` →
  `POST /auth/password-reset/`
- `authService.confirmPasswordReset({ uid, token, new_password, confirm_password })` →
  `POST /auth/password-reset/confirm/`
- Both reuse the existing `apiClient` (single HTTP client with the token
  refresh interceptor) and `getApiErrorMessage` / `normalizeApiError`.
- `hooks/usePasswordReset.ts` exposes `useRequestPasswordReset` and
  `useConfirmPasswordReset` React Query mutations.

## Design consistency

Both new pages reuse the existing Saamu Tailors design language from Login:
branding banner, white rounded card, `#1E3A8A` buttons, `#F8FAFC` background,
same typography/spacing/alert styles. No redesign of the auth system was made.
