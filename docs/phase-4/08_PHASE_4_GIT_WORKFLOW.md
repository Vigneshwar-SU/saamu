# Saamu Tailors — Phase 4 Git Workflow

From Phase 4 onward, Git is part of phase completion.

## Before work
Inspect:
```text
git status
git branch --show-current
git log --oneline -5
```
Do not overwrite unrelated changes.

## Never commit
`.env`, secrets, passwords, PostgreSQL credentials, local DBs, node_modules, virtual environments, logs, build artifacts or temporary files.

## After verification
Inspect:
```text
git status
git diff --stat
git diff
```
Review for secrets, unrelated changes, debug code and generated junk.

Commit with a focused message such as:
```text
feat(orders): implement phase 4 order management
```

After user review/approval:
```text
git push
```

If no upstream exists, report the exact required command rather than guessing.

## Completion report must contain
Implementation, files, migrations, endpoints, RBAC, tests, build/lint, manual verification, known issues, deferred items, commit hash and push result.

Do not claim complete until Git status and push outcome are explicitly reported.
