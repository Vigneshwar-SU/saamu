# Phase 20 — Architecture

## Architectural Goal
Make the application portable between:
- local Windows + PostgreSQL
- a cloud-hosted Django runtime + PostgreSQL

## Principles
- Environment configuration without requiring a specific hosting platform.
- PostgreSQL remains the database engine.
- Django remains authoritative for application behavior.
- Phase 16 db_backup/db_restore remain the portability primitives.
- No business logic should know whether PostgreSQL is local or remote.

## Configuration Boundary
Application configuration should derive connection information from environment variables such as:
- DATABASE_NAME
- DATABASE_USER
- DATABASE_PASSWORD
- DATABASE_HOST
- DATABASE_PORT

Inspect existing project conventions before introducing or renaming variables.

## Operational Boundary
Database:
- PostgreSQL backup/restore.

Not database:
- uploaded media
- static/build output
- .env and credentials
- logs
- source code

Phase 16 explicitly distinguishes these categories and states that pg_dump does not automatically include the non-database assets.

## Deployment Boundary
The application must not assume:
- Windows-only filesystem paths
- a localhost database
- PostgreSQL binaries being installed beside the source tree
- writable source-tree backup directories

## No New Persistence
Cloud migration readiness itself must not create a business model, migration record, or CloudDeployment table.
