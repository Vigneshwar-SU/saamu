Phase — Email-Based Password Reset
Status

Implementation: PENDING
Manual Verification: PENDING

1. Objective

Implement a proper email-based Forgot Password / Password Reset feature for Saamu Tailors.

The current Forgot Password functionality is only a placeholder. This phase will replace it with a complete, secure, real-world password-reset workflow.

The feature will use email verification links rather than OTP-based password resets.

2. Real-World Workflow

The system will support three accounts:

Owner
Staff
Shop/Admin email

The shop email currently available for development and real testing is:

saamutailors1954@gmail.com

The shop email will be used as the operational email address for the system's password-reset emails during this stage.

Password reset flow
Login Page
    ↓
Forgot Password?
    ↓
Enter registered email
    ↓
Backend checks the account
    ↓
Password-reset email is generated
    ↓
Email contains secure reset link
    ↓
User clicks the link
    ↓
Reset Password page opens
    ↓
Enter new password
    ↓
Confirm new password
    ↓
Backend validates reset token
    ↓
Password is changed
    ↓
Token becomes unusable
    ↓
User returns to Login
3. Important Security Requirement

The system must never send the existing password through email.

It must also never expose whether a particular email address exists in the system.

For example, when a user enters:

someone@example.com

the UI should respond with a generic message such as:

If an account exists for this email address,
a password reset link has been sent.

This prevents attackers from discovering registered accounts.

4. Backend Implementation
4.1 Password Reset Request Endpoint

Create:

POST /api/v1/auth/password-reset/
Request
{
    "email": "saamutailors1954@gmail.com"
}
Response

Always return a generic success response.

Example:

{
    "success": true,
    "message": "If an account exists for this email address, a password reset link has been sent."
}

Do not reveal whether the account exists.

5. Password Reset Token

Use Django's built-in password-reset token mechanism wherever possible.

Do not implement a custom insecure token system.

The reset token must:

Be cryptographically safe.
Be time-limited.
Be tied to the user.
Become invalid after the password is changed.
Not expose the user's password.
Not be stored as plain text in the database.
6. Password Reset Confirmation Endpoint

Create:

POST /api/v1/auth/password-reset/confirm/
Request
{
    "uid": "<encoded-user-id>",
    "token": "<reset-token>",
    "new_password": "<new-password>",
    "confirm_password": "<new-password>"
}

The backend must:

Decode the user ID.
Find the user.
Validate the reset token.
Validate the new password.
Ensure both passwords match.
Change the password.
Invalidate the reset token.
Return success.
7. Password Validation

Use Django's password validators.

The backend must reject weak passwords according to the project's configured password-validation rules.

At minimum, the frontend should provide:

New password.
Confirm password.
Password visibility toggle.
Password mismatch validation.
Required-field validation.
Clear validation messages.

The backend remains authoritative.

Frontend validation must never replace backend validation.

8. Email Configuration

During development, configure Django to send actual emails through Gmail SMTP.

The shop email:

saamutailors1954@gmail.com

will be used as the sender.

Do not place the Gmail password directly inside:

settings.py

or commit it to Git.

Use environment variables.

Example:

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=saamutailors1954@gmail.com
EMAIL_HOST_PASSWORD=<gmail-app-password>
DEFAULT_FROM_EMAIL=saamutailors1954@gmail.com
9. Gmail App Password

The normal Gmail account password should not be placed in Django.

Use a Gmail App Password.

The development setup should therefore be:

Gmail Account
      ↓
2-Step Verification
      ↓
App Password
      ↓
Django SMTP
      ↓
Password Reset Email

The App Password must be stored only in the local .env file.

10. .env Security

Ensure the project's environment file is ignored by Git.

.gitignore should contain:

.env
.env.*
!.env.example

Create or update:

.env.example

with placeholders only:

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-shop-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-shop-email@gmail.com

Never commit:

EMAIL_HOST_PASSWORD=<real-password>
11. Frontend — Forgot Password

Replace the current placeholder behaviour.

The Login page should have:

Forgot Password?

When clicked:

Forgot Password
────────────────────────────

Enter your registered email

[ Email Address                ]

[ Send Reset Link ]

Back to Login

After submission:

Check your email

If an account exists for this email address,
we've sent a password reset link.

Please check your inbox and spam folder.

[ Back to Login ]

Do not reveal whether the account exists.

12. Frontend — Reset Password Page

Create a dedicated route:

/reset-password/:uid/:token

Example:

http://localhost:5173/reset-password/<uid>/<token>

Page:

Reset Password
────────────────────────

Create a new password

New Password
[ **************** ]

Confirm Password
[ **************** ]

[ Reset Password ]

After successful reset:

Password Reset Successful

Your password has been changed successfully.

[ Go to Login ]
13. Invalid / Expired Link

If the token is invalid or expired, show:

Reset Link Invalid

This password reset link is invalid or has expired.

Please request a new password reset link.

[ Request New Link ]

Do not expose internal backend errors.

14. Email Design

The email should look professional and appropriate for Saamu Tailors.

Suggested content:

Saamu Tailors

Password Reset Request

Hello,

We received a request to reset the password
for your Saamu Tailors account.

Click the button below to create a new password.

[ Reset Password ]

This link is temporary and can only be used once.

If you did not request a password reset,
you can safely ignore this email.

Regards,
Saamu Tailors

The email should include:

Saamu Tailors branding.
Clear reset button.
Reset URL fallback text.
Security warning.
No password.
No sensitive account information.
15. Reset Link Configuration

The backend must generate the frontend URL rather than pointing the user to a Django page.

Development:

http://localhost:5173/reset-password/<uid>/<token>

Do not hard-code this throughout the application.

Use an environment/configuration value.

Example:

FRONTEND_URL=http://localhost:5173

Then construct:

${FRONTEND_URL}/reset-password/${uid}/${token}

This will make the feature easier to migrate to production later.

16. Authentication Behaviour

After the password is successfully changed:

Existing password must no longer work.
New password must work.
Reset token must no longer work.
User should be redirected to Login.
User should authenticate normally using the new password.

The system must not automatically log the user in after resetting the password unless explicitly designed later.

17. OWNER / STAFF Compatibility

The password reset mechanism should work for both:

OWNER
STAFF

No separate password-reset implementation should be created for each role.

The reset process is account-based.

Example:

Owner account
    ↓
Forgot password
    ↓
Owner's registered email
    ↓
Reset link
    ↓
New password

and:

Staff account
    ↓
Forgot password
    ↓
Staff's registered email
    ↓
Reset link
    ↓
New password

The user's role must remain unchanged.

18. Account Email Requirement

The password-reset feature depends on each account having a valid email address.

Therefore, verify the current User model.

The implementation must determine whether the existing user model already supports:

email

If it does, reuse it.

Do not create another email field or duplicate user model.

If the current system does not enforce unique emails, evaluate whether password reset can safely identify users.

Do not silently introduce a breaking database change.

19. API Error Handling

The frontend must correctly handle:

Network failure
Unable to connect to the server.
Please try again.
Invalid reset token
This reset link is invalid or expired.
Weak password

Display backend validation errors clearly.

Password mismatch
Passwords do not match.
Rate limiting / repeated requests

The implementation should avoid allowing unlimited password-reset email requests.

If rate limiting is already available in the project, reuse it.

Otherwise, document rate limiting as a production hardening requirement rather than introducing an unrelated authentication framework.

20. Frontend React Query / API Integration

Create or extend the authentication service.

Example functions:

requestPasswordReset(email)
confirmPasswordReset(uid, token, newPassword, confirmPassword)

Use the project's existing Axios/API infrastructure.

Do not create a second HTTP client.

21. UI Requirements

Keep the existing Saamu Tailors design language.

The new pages should follow the existing:

Typography.
Spacing.
Buttons.
Inputs.
Border radius.
Error alerts.
Loading states.
Responsive behaviour.

Do not redesign the entire authentication system during this phase.

The broader Login UI changes will be handled separately after the password-reset functionality is verified.

22. Loading States

When sending reset email:

Sending...

Disable the submit button while the request is in progress.

When resetting the password:

Resetting Password...

Disable duplicate submissions.

23. Automated Tests

Add backend tests for:

Password reset request
Anonymous user can request reset.
Existing email produces a reset email.
Unknown email returns the same generic response.
No account enumeration occurs.
Email contains the reset link.
Email does not contain the password.
Password reset confirmation
Valid token successfully resets password.
Invalid token is rejected.
Expired token is rejected.
Used token is rejected.
Password mismatch is rejected.
Weak password is rejected.
Old password no longer works.
New password works.
User role remains unchanged.
Authorization / security

Password reset should not require the user to already be authenticated.

24. Frontend Verification

Verify:

Forgot Password link works.
Email form renders correctly.
Validation works.
Loading state works.
Generic success message works.
Reset email is received.
Reset link opens correctly.
Reset page loads.
Password visibility toggle works.
Password mismatch is displayed.
Successful reset works.
Invalid token state works.
Expired token state works.
Login with new password works.
Old password fails.
25. Manual Testing With Real Email

Use:

saamutailors1954@gmail.com

for real email testing.

Test with an actual account registered in the system.

Test flow
1. Open Login
2. Click Forgot Password
3. Enter registered email
4. Click Send Reset Link
5. Open Gmail
6. Find the Saamu Tailors email
7. Click Reset Password
8. Enter a new password
9. Confirm password
10. Submit
11. Return to Login
12. Login with the new password
13. Confirm old password no longer works
14. Try using the reset link again
15. Confirm it is rejected
26. Important Development Note

The feature should use real Gmail SMTP, not Django's console email backend, for this implementation.

The local development environment is only where Django runs.

The actual email delivery will happen through:

Saamu Tailors Django Backend
        ↓
Gmail SMTP
        ↓
saamutailors1954@gmail.com
        ↓
Real Gmail Inbox

This means the feature can be manually tested with a real email account before production deployment.

27. Production Migration Consideration

The architecture should make it possible to later replace Gmail SMTP with a dedicated transactional email provider.

For example:

Development
Django → Gmail SMTP

Production
Django → Transactional Email Provider

The application code should not be tightly coupled to Gmail.

Only the email configuration should change.

28. Files Expected
Backend

Potential files:

backend/
├── apps/
│   └── authentication/
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── tests/
│           └── test_password_reset.py

Use the existing project structure instead of creating unnecessary files.

Frontend

Potential files:

frontend/src/
├── pages/
│   ├── ForgotPassword.tsx
│   └── ResetPassword.tsx
├── services/
│   └── authService.ts
├── types/
│   └── auth.ts
└── routes/
    └── AppRoutes.tsx

Reuse existing authentication utilities wherever possible.

29. Migration Requirement

Before implementation:

python manage.py makemigrations --check --dry-run

After implementation:

python manage.py migrate --plan

Do not create migrations unless the existing architecture genuinely requires a database change.

30. Verification Requirements

Run:

python manage.py check

Backend tests:

python manage.py test

Frontend:

npm run lint
npm run build

TypeScript:

npx tsc --noEmit

All existing tests must continue to pass.

31. Definition of Done

The phase is complete only when:

 Forgot Password is no longer a placeholder.
 User can submit an email.
 Real email is delivered.
 Reset link works.
 Reset page works.
 New password can be created.
 Password confirmation works.
 Invalid tokens are rejected.
 Expired tokens are rejected.
 Used tokens cannot be reused.
 Old password stops working.
 New password works.
 OWNER account works.
 STAFF account works.
 Generic responses prevent email enumeration.
 Backend remains authoritative.
 Real email credentials are not committed.
 Automated backend tests pass.
 TypeScript passes.
 ESLint passes.
 Frontend build passes.
 Existing authentication functionality remains intact.
 Manual verification is completed separately.
32. Implementation Rules
Do not rebuild the existing authentication system.
Do not create a second User model.
Reuse Django's secure password-reset mechanisms wherever possible.
Do not expose whether an email exists.
Do not send passwords through email.
Do not store Gmail credentials in source code.
Do not commit .env.
Do not weaken OWNER/STAFF RBAC.
Do not automatically log users in after password reset.
Do not modify unrelated modules.
Do not perform broad UI redesign during this phase.
Do not break existing authentication/login behaviour.
Keep the implementation production-migration friendly.
Run all existing automated tests before declaring completion.
Clearly report any pre-existing failures separately from newly introduced failures.
33. Completion Report

After implementation, create:

docs/
└── password-reset/
    └── COMPLETION_REPORT.md

The completion report must contain:

Implementation status.
Backend changes.
Frontend changes.
API endpoints.
Email configuration.
Security considerations.
Files changed.
Migration status.
Automated test results.
Frontend build results.
Known issues.
Manual verification status.

Manual verification must initially be marked:

PENDING

until the project owner performs the real Gmail-based verification.