# Password Reset — Security

## Account enumeration prevention

- The request endpoint always returns
  `"If an account exists for this email address, a password reset link has been sent."`
  for a well-formed request, whether or not the account exists.
- Emails are only sent for existing **active** accounts; unknown and inactive
  accounts silently get no email — the HTTP response is identical either way.
- The confirm endpoint returns one generic `invalid_reset_token` error for any
  unusable link, so nothing about the user or the token internals is revealed.
- Case-insensitive email lookup (`email__iexact`) does not leak the stored
  casing.

## Token security

- Uses Django's built-in `PasswordResetTokenGenerator`: a salted HMAC digest
  over user id, password hash, login timestamp, email and issue timestamp.
- Tokens are time-limited (`PASSWORD_RESET_TIMEOUT`, default 15 minutes).
- Tokens are tied to the user and automatically invalidated when the password
  changes (the password hash is part of the digest) — this also means a token
  issued *before* a password change cannot be used *after* it.
- Raw tokens are never stored: only the SHA-256 digest is persisted
  (`PasswordResetToken.token_hash`), and the record is marked `used`/`used_at`
  after a successful reset. Reuse is rejected.
- No passwords are ever sent over email.

## Password policy

- Django `AUTH_PASSWORD_VALIDATORS` are authoritative (similarity, minimum
  length, common-password, numeric-only checks).
- The token is consumed only **after** the new password passes validation, so a
  weak-password attempt never burns a valid link.

## Rate limiting

- Both public endpoints use DRF `ScopedRateThrottle` (no new dependency):
  `password_reset_request` (default `5/hour`) and `password_reset_confirm`
  (default `30/hour`), overridable per environment. Abused clients receive
  HTTP 429 with the standardized `throttled` error.
- Scoped throttles only affect the endpoints that opt in; the rest of the API
  is unaffected.

## Isolation

- Reset endpoints are public and require no JWT; they cannot be used to obtain
  or invalidate sessions.
- After a successful reset the user is **not** auto-logged-in; login continues
  to work exactly as before (username + password).
- Reset changes only the password: role, username, `is_active` and permissions
  are preserved. OWNER/STAFF RBAC is unchanged.
- Existing authentication/login/JWT behaviour is untouched.

## Production configuration guard

With `DEBUG=False`, startup validation requires `EMAIL_HOST`,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` and a
non-loopback `FRONTEND_URL`, so a production deployment cannot silently run
without email working. Validation messages never include secret values.

## Account email requirement

The password-reset flow depends on accounts having a valid email address. The
existing `User` model's `email` field (from `AbstractUser`) is reused — no new
field or user model was created, and no breaking database change was introduced.
Emails are not globally unique; because each user id is encoded in the uid and
bound into the token digest, reset links remain unambiguous per account.
