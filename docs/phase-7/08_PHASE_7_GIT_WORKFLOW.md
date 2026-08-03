# Phase 7 — Git & Documentation Workflow

## Before Implementation
- Confirm branch and working tree.
- Read Phase 1–6 completion reports as needed.
- Do not modify unrelated features.

## Before Commit
```powershell
git status
git diff --stat
```

Confirm Phase 7 docs are included and no secrets/unrelated changes are present.

## PASS Gate
A phase is PASS only after:
1. Backend checks pass.
2. Full regression tests pass.
3. Frontend lint/tsc/build pass.
4. Manual browser verification passes.
5. Completion report is updated with actual results.
6. Commit is created.
7. Push to `origin master` succeeds.
8. `git rev-parse HEAD` equals `git rev-parse origin/master`.
9. Working tree is clean.

## Suggested Commit
`feat(payments): implement phase 7 payroll settlement`

Do not claim push success without command output confirming it.
