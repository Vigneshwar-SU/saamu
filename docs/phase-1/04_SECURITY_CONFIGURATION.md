# Security Configuration

## Objective
Establish safe defaults before business functionality is introduced.

## Secrets
Never commit `.env`, real DB passwords, secret keys, JWT secrets, API credentials, or messaging credentials. Commit `.env.example` templates only.

## API Permissions
Default DRF access must not be open to everyone. Use authenticated access as the default foundation. Explicit public endpoints must be intentional.

## Authentication
JWT is the selected authentication foundation. Phase 1 prepares it; Phase 2 implements login/token flow and OWNER/STAFF authorization.

## CORS
Environment-driven. No unrestricted wildcard production configuration.

## Error Disclosure
Do not expose stack traces, filesystem paths, credentials, environment variables, or internal implementation details.

## Logging Safety
Never log passwords, tokens, secrets, or unnecessary sensitive customer information.

## Validation
Backend validation is authoritative. Frontend validation is UX support, not a security boundary.

## Database
PostgreSQL only; never introduce SQLite fallback.

## File Handling
No developer-specific absolute paths.

## Scope
No business authorization or audit UI in Phase 1.
