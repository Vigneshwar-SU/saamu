# Password Reset — Automated Testing

## Backend

`backend/apps/authentication/tests/test_password_reset.py` (26 tests, all
passing). Uses the in-memory email backend (`locmem`) and clears the throttle
cache between tests.

### Request endpoint
- Anonymous (unauthenticated) requests are accepted.
- Existing email produces exactly one reset email with the correct subject,
  recipient and a parseable `/reset-password/<uid>/<token>` link.
- Unknown email returns the same generic success message and sends no email.
- The response is byte-identical for existing vs unknown emails (no
  enumeration).
- The email body contains the reset link but never the password.
- Malformed email → 400 `validation_error`.
- Inactive account → generic response, no email.
- Both OWNER and STAFF emails produce reset emails.
- Email lookup is case-insensitive.

### Token behaviour
- Valid token changes the password and marks the record used.
- Invalid token → generic `invalid_reset_token`.
- Malformed uid, non-numeric uid and nonexistent uid → generic
  `invalid_reset_token`.
- Expired token (simulated by back-dating the generator clock) → rejected.
- Token is single-use: a second submit with the same link is rejected.
- A token is invalidated if the password is changed out-of-band beforehand.

### Confirm endpoint
- Requires no authentication.
- Mismatched passwords → 400 `validation_error` on `confirm_password`.
- Weak password → 400 `validation_error` on `new_password` and the token is
  **not** consumed.
- Empty password → 400 `validation_error`.
- Role, username and `is_active` are preserved after a reset (OWNER and STAFF).
- After a reset, login succeeds with the new password and fails with the old
  one; the user role in the login response is unchanged.

### Rate limiting
- Exceeding the `password_reset_request` scope (default 5/hour in tests)
  returns HTTP 429 with the standardized `throttled` error.

## Frontend verification

Automated:
- `npm run lint` — clean (0 errors, `--max-warnings 0`).
- `npx tsc --noEmit` — passes.
- `npm run build` — passes (only the pre-existing chunk-size warning).

Manual UI verification steps are listed in `07-manual-verification.md`.

## Full verification commands

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe -m pytest            # 800 passed

cd frontend
npm run lint
npx tsc --noEmit
npm run build
```
