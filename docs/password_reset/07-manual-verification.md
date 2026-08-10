# Password Reset — Manual Verification

Status: PENDING

The project owner must perform the real Gmail-based verification. The automated
suite already covers the functional and security behaviour; this document
covers the end-to-end manual checks, including real email delivery.

## Prerequisites

1. Backend running (`manage.py runserver`) and frontend running (`npm run dev`).
2. The local `backend/.env` has a real Gmail App Password in
   `EMAIL_HOST_PASSWORD` (see `04-email-configuration.md`). **Never commit it.**
3. At least one account (OWNER and one STAFF) exists with its `email` field set
   to `saamutailors1954@gmail.com` (or another inbox you can read).
4. The reset email is sent from `saamutailors1954@gmail.com`; open that inbox to
   verify delivery.

## End-to-end flow

1. Open `/login`.
2. Click **Forgot Password?** → the Forgot Password page opens.
3. Enter a registered email and click **Send Reset Link**; the button shows
   **Sending...** and is disabled during the request.
4. The generic success message appears ("If an account exists with this email
   address, a password reset link has been sent.") and no account-specific
   detail is shown.
5. Open the inbox and find the **Saamu Tailors — Password Reset Request** email
   with the branded **Reset Password** button.
6. Click the reset link → `/reset-password/<uid>/<token>` opens the Reset
   Password page.
7. Enter a new password, confirm it, toggle the visibility icons, and submit.
   The button shows **Resetting Password...**.
8. The success panel appears ("Password Reset Successful").
9. Return to Login and sign in with the **new** password — it works.
10. Sign out and confirm the **old** password no longer works.
11. Try the same reset link again → the "Reset Link Invalid" state appears with
    a **Request New Link** button (single-use enforcement).

## Enumeration / anti-abuse checks

1. Submit a random unregistered email → identical generic success message,
   no email is sent.
2. Submit a malformed email → inline validation error, no request sent.
3. Submit more than 5 reset requests in an hour → HTTP 429 (rate limited).
4. Confirm the request response never reveals whether the account exists.

## Edge cases

1. Open `/reset-password/abc/def` (malformed link) → "Reset Link Invalid" state.
2. Open `/reset-password/` without parameters → "Reset Link Invalid" state.
3. Set `PASSWORD_RESET_TIMEOUT` to a tiny value (or wait 15 minutes) and use an
   expired link → rejected with the generic invalid-link state.
4. Request a reset, then change the password via a previous reset → the old
   link is rejected.
5. Verify OWNER and STAFF accounts both complete the flow and their **role
   remains unchanged** after the reset.

## Result recording

Record the outcome of every check above in `COMPLETION_REPORT.md`. Only mark
Manual Verification DONE when all steps pass with real email delivery confirmed.
