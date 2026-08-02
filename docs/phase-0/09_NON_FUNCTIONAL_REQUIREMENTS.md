# Saamu Tailors — Non-Functional Requirements

## Usability

The software is used by people working in a real tailoring shop.

Therefore:

- Common actions should require minimal clicks.
- Search should be fast.
- Forms should be clear.
- Error messages should be understandable.
- Important information should be visually obvious.
- Avoid unnecessary technical terminology.

## Performance

For the initial single-PC deployment:

- Normal pages should load quickly.
- Search should be responsive.
- Dashboard queries should be efficient.
- Avoid unnecessary API requests.

## Reliability

The application should handle:

- Restarting the PC.
- Restarting Django.
- Restarting PostgreSQL.
- Temporary application errors.

Business data must remain persistent.

## Data integrity

Critical data must be validated on the backend.

Financial calculations must use precise monetary types.

Do not use floating-point arithmetic for money where exact decimal arithmetic is required.

## Security

- Passwords must be hashed.
- JWT must be secured appropriately.
- Secrets must not be committed.
- Backend authorization must be enforced.
- Input must be validated.
- Internal errors must not be exposed to users.
- CORS must be intentionally configured.

## Backup

Local deployment must have a practical database backup process.

Backup and restore should be tested before production use.

## Maintainability

Code should:

- Be modular.
- Be readable.
- Avoid duplication.
- Use clear naming.
- Have reasonable separation of concerns.
- Include tests for important business logic.

## Scalability

The architecture should support future:

- More users
- More orders
- More customers
- Cloud deployment
- Multiple branches
- Additional notification providers

without requiring a full rewrite.

## Compatibility

Version 1 target:

- Windows desktop
- Modern Chromium-based browser
- Local network/local machine deployment

## Accessibility

Use reasonable:

- keyboard navigation
- readable contrast
- form labels
- focus states
- clear validation messages

## Observability

The application should have:

- structured application logging
- error logging
- audit logging for important business actions
- health check endpoint

## Deployment principle

Environment-specific configuration must remain outside business code.

The same application should be capable of running in local development, local production-like deployment, and future cloud deployment using environment configuration.
