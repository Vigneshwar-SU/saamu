# Phase 16 — Testing

## Backup tests
Cover:
- authenticated access where applicable
- OWNER/STAFF authorization
- backup naming
- controlled backup location
- successful backup result
- failed backup process
- missing PostgreSQL tooling
- inaccessible backup directory
- invalid backup identifier/path
- secret non-disclosure

## Restore tests
Cover:
- explicit authorization
- confirmation requirement
- invalid/unavailable backup
- pre-restore safety behavior
- restore failure handling
- post-restore connectivity/integrity verification
- no arbitrary command/path execution
- no accidental mutation through ordinary GET/read endpoints

## Portability tests
Where practical, verify that a generated backup is recognized by PostgreSQL tooling and that the documented restore workflow is internally consistent.

Do not run destructive restore tests against the live shop database.

## Regression gates
Backend:
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- focused pytest
- full pytest
- black
- isort

Frontend, if changed:
- `npm run lint`
- `npx tsc --noEmit`
- `npm run build`

Manual backup/restore against real shop data remains separate and must stay NOT STARTED until the user performs it.
