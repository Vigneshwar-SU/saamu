# Git, Environment and Configuration

## Git
If Git is not initialized, initialize it. Never reset/destroy existing user work.

Suggested baseline commit:
```text
chore: establish Saamu Tailors project foundation
```

## .gitignore
Exclude at least:
```text
.env
.env.*
!.env.example
node_modules/
dist/
build/
.venv/
venv/
env/
__pycache__/
*.pyc
media/
staticfiles/
logs/
*.log
IDE/editor temporary files
OS temporary files
```

Do not accidentally ignore source or documentation.

## Environment
Real `.env` files are local-only. `.env.example` is the committed template. Never place real credentials in examples.

## Paths
Avoid absolute machine-specific paths. Prefer project-relative or environment-driven configuration.

## Reproducibility
README must explain:
1. backend environment setup
2. dependency installation
3. PostgreSQL setup
4. `.env` setup
5. Django checks
6. backend startup
7. frontend installation
8. frontend environment
9. frontend startup
10. build/lint/type checks

## Local-First
No cloud services merely for future use.

## Migration Ready
Make database host, allowed hosts, CORS, storage, logging and secrets configurable without rewriting business logic.

## Documentation
Document only functionality that actually exists.
