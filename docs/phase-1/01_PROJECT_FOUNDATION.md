# Project Foundation

## Objective
Create a clean, reproducible foundation for the local Windows deployment while keeping the architecture ready for later cloud migration.

## Architecture
```text
React + TypeScript
        |
        | REST API
        v
Django REST Framework
        |
        v
PostgreSQL
```

## Repository
Expected high-level structure:
```text
saamu/
├── backend/
├── frontend/
├── docs/
│   ├── phase-0/
│   └── phase-1/
├── prompts/
├── .gitignore
└── README.md
```

Inspect existing work first. Never blindly overwrite valid files.

Normalize accidental documentation nesting to `docs/phase-0/` and `docs/phase-1/`.

## Python Environment
Use one backend virtual environment, preferably:
```text
backend/.venv/
```
Do not commit it or maintain unnecessary duplicate environments.

## Dependency Discipline
Only use dependencies justified by Phase 0 and Phase 1. Do not add Redis, Celery, Docker, Kubernetes, queues, or cloud services unless explicitly required.

## Local-First
The application initially runs on one Windows PC inside the shop.

Avoid machine-specific absolute paths.

## Cloud Compatibility
Deployment-specific configuration must be separable from application code so database, hosts, CORS, storage, logging, and secrets can change later without rewriting business logic.
