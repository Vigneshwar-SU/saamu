# Phase 16 — Backup & Restore Runbook

## Purpose
Operational procedure for protecting and recovering Saamu Tailors PostgreSQL data.

## Before backup
- Confirm PostgreSQL is reachable.
- Confirm backup destination exists and has sufficient disk space.
- Confirm backup destination is outside the source tree.
- Confirm credentials are supplied through the environment/tooling and are not written into scripts or logs.

## Backup
Use the repository's approved PostgreSQL-native command/procedure.

Record:
- timestamp
- backup filename
- database/source environment
- success/failure
- verification result

## Backup verification
- Confirm the backup artifact exists.
- Confirm it is non-empty.
- Inspect it with PostgreSQL tooling.
- Prefer a test restore to a throwaway database before considering a backup proven recoverable.

## Restore safety
1. Stop or restrict application writes as required.
2. Create a fresh pre-restore safety backup.
3. Confirm the target database is the intended target.
4. Restore only the selected known backup.
5. Run database/application integrity checks.
6. Re-enable application access.
7. Verify critical business records.

## Never
- test destructive restore against the live database
- overwrite the only known-good backup
- paste credentials into shell history or source code

## Recovery failure
Document the failure and preserve:
- the pre-restore safety backup
- the original backup
- logs needed to diagnose the issue

Do not claim recovery success without post-restore verification.
