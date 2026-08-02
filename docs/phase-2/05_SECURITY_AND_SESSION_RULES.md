# Security and Session Rules

## Passwords
Use Django password hashing. Never store, log, return, or expose plaintext passwords or password hashes.

## JWT
Keep SimpleJWT centralized. Never hard-code secret keys.

## Refresh Security
Use proper token invalidation for logout. If blacklist is used, configure migrations and test it.

## Token Storage
Use one token-storage mechanism based on the Phase 1 service. Document the chosen browser storage approach and trade-offs.

## XSS
Do not render tokens or untrusted values as raw HTML. Avoid unnecessary `dangerouslySetInnerHTML`.

## CSRF
JWT bearer authentication is distinct from cookie-session authentication. Do not add cookie auth unless explicitly required.

## CORS
Keep environment-driven CORS. Do not loosen it to make authentication work.

## Rate Limiting
Do not build a complex security subsystem in this phase. Document the current throttling state if applicable.

## User Enumeration
Invalid login responses must not reveal whether an account exists.

## Role Tampering
Never trust a role supplied by React. Backend authorization must use the authenticated database user.

## Superuser
Document Django superuser handling without introducing a third application role.

## Security Tests
Verify anonymous denial, invalid credentials, valid login, invalid/expired tokens, refresh, logout invalidation, and server-side OWNER/STAFF authorization.
