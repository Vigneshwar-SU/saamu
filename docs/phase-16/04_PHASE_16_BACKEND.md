# Phase 16 — Backend

## Required review
Inspect the existing Phase 15 backup/restore documentation and current Django settings before implementation.

## Implementation rules
- Reuse environment-driven PostgreSQL configuration.
- Reuse the existing exception/error contract.
- Never expose `DATABASES`, passwords, `SECRET_KEY`, or other secrets in API responses.
- Never accept arbitrary executable commands from a request.
- Never accept an arbitrary restore target supplied by the client.
- Restrict any application-facing backup/restore action to an explicit permission policy.
- Validate backup names, paths, and selected backup identifiers server-side.
- Use subprocess execution only with fixed executable/argument structures and controlled paths if application code genuinely needs it.
- Handle process failure, missing binaries, inaccessible storage, corrupted/incomplete backup files, and database connection failures explicitly.
- Keep backup and restore operations outside ordinary request timeouts if the implementation requires long-running work; otherwise document the operational limitation rather than pretending the action is asynchronous.
- Do not block normal shop operations unnecessarily for routine backups.

## Verification
Run:
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused Phase 16 tests
- full pytest suite
- black
- isort

If no backend code is required, document why and verify the operational procedure instead.
