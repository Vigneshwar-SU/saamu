# Password Reset — Backend

## Endpoints

### 1. Request a reset link

`POST /api/v1/auth/password-reset/`

Request body:

```json
{
  "email": "saamutailors1954@gmail.com"
}
```

Response (always, regardless of whether the account exists):

```json
{
  "success": true,
  "message": "If an account exists for this email address, a password reset link has been sent."
}
```

Behaviour:

- Public: no authentication required (`permission_classes = []`,
  `authentication_classes = []`).
- Rate limited via `ScopedRateThrottle` scope `password_reset_request`
  (default `5/hour`, overridable with `PASSWORD_RESET_REQUEST_RATE`).
- A reset email is only sent when an **active** (`is_active=True`) account
  matches the email (case-insensitive). OWNER and STAFF are treated the same.
- Invalid email format → 400 `validation_error` (this reveals nothing about
  account existence).

### 2. Apply a new password

`POST /api/v1/auth/password-reset/confirm/`

Request body:

```json
{
  "uid": "<urlsafe-base64 user id>",
  "token": "<reset token>",
  "new_password": "<new password>",
  "confirm_password": "<new password>"
}
```

Success response:

```json
{
  "success": true,
  "message": "Your password has been reset successfully."
}
```

Behaviour:

- Public, rate limited via scope `password_reset_confirm` (default `30/hour`,
  overridable with `PASSWORD_RESET_CONFIRM_RATE`).
- Any unusable link (malformed uid, unknown/inactive user, invalid/expired/
  already-used token) returns the same generic error so nothing is leaked:

```json
{
  "success": false,
  "error": {
    "code": "invalid_reset_token",
    "message": "The password reset link is invalid or has expired."
  }
}
```

- Password mismatch → 400 `validation_error` with
  `details.confirm_password = "Passwords do not match."`
- Weak passwords (Django `AUTH_PASSWORD_VALIDATORS`) → 400 `validation_error`
  with `details.new_password = [...]`. The token is **not** consumed by a
  failed password attempt; it is only marked used after validation passes.

## Token & Storage Design

- `PasswordResetTokenGenerator` (stateless, Django built-in) creates tokens
  from a salted HMAC digest of the user id + password hash + login timestamp +
  email + issued-at timestamp. Changing the password automatically invalidates
  every outstanding token.
- A `PasswordResetToken` model row enforces single use: it stores only
  `hash_token(token)` (SHA-256 hex), `used`, and `used_at`. The raw token is
  emailed and never persisted.
- Expiry comes from Django's `PASSWORD_RESET_TIMEOUT` (default 900 s = 15 min).
- Stale rows are pruned opportunistically on each request
  (`_prune_expired_records`).

## Configuration

Environment-driven (see `04-email-configuration.md`):

- `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `FRONTEND_URL`, `PASSWORD_RESET_TIMEOUT`
- `PASSWORD_RESET_REQUEST_RATE`, `PASSWORD_RESET_CONFIRM_RATE` (optional)

With `DEBUG=False`, production startup validation also requires
`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
and a non-loopback `FRONTEND_URL`.

## Migration

`authentication.0003_passwordresettoken` creates the `PasswordResetToken`
model with indexes on (`user`, `used`) and (`token_hash`). Verified with
`makemigrations --check --dry-run` (no pending changes) and `migrate --plan`.
