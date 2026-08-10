# Password Reset — Email Configuration

## Gmail SMTP via environment variables

Django is configured to send real email through Gmail SMTP. All values are
environment-driven (`.env`), so production can later switch to a transactional
email provider by changing configuration only — the application code is not
coupled to Gmail.

| Variable | Development value | Notes |
| --- | --- | --- |
| `EMAIL_BACKEND` | (empty → `django.core.mail.backends.smtp.EmailBackend`) | Override only if needed |
| `EMAIL_HOST` | `smtp.gmail.com` | |
| `EMAIL_PORT` | `587` | |
| `EMAIL_USE_TLS` | `True` | |
| `EMAIL_HOST_USER` | `saamutailors1954@gmail.com` | |
| `EMAIL_HOST_PASSWORD` | *(Gmail App Password, local only)* | Never commit |
| `DEFAULT_FROM_EMAIL` | `Saamu Tailors <saamutailors1954@gmail.com>` | |
| `FRONTEND_URL` | `http://localhost:5173` | Base for the reset link |
| `PASSWORD_RESET_TIMEOUT` | `900` | Reset link lifetime in seconds (15 min) |
| `PASSWORD_RESET_REQUEST_RATE` | `5/hour` (optional) | |
| `PASSWORD_RESET_CONFIRM_RATE` | `30/hour` (optional) | |

The reset link is built in code as
`${FRONTEND_URL.rstrip('/')}/reset-password/<uidb64>/<token>`, never hard-coded.

## Gmail App Password

Gmail does not allow the normal account password for SMTP. Use an App Password:

1. Enable **2-Step Verification** on the Google account.
2. Google Account → **Security** → **App passwords**.
3. Create an app password for the Saamu Tailors application.
4. Put it in the local `.env` file only:

```ini
EMAIL_HOST_PASSWORD=<gmail-app-password>
```

## Secrets safety

- `backend/.env` is git-ignored (`.gitignore` contains `.env`, `.env.*`,
  `!.env.example`).
- `backend/.env.example` ships placeholders only and is the template for any
  deployment. Real credentials are never committed.
- Production startup (`DEBUG=False`) refuses to boot until `EMAIL_HOST`,
  `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and `DEFAULT_FROM_EMAIL` are
  provided (see `config/configuration_validation.py`). Error messages name only
  the configuration category, never secret values.

## Email content

Templates: `backend/apps/authentication/templates/authentication/password_reset_email.{html,txt}`.

The email includes:

- Saamu Tailors branding.
- A clear **Reset Password** button (HTML) with a plain-text URL fallback.
- The reset link expiry (15 minutes) and a "link can only be used once" notice.
- A warning that the email can be safely ignored if the request was not made.
- **No password and no sensitive account information.**
