# Saamu Tailors — Architecture Decisions

## 1. Architecture style

Use a separated frontend/backend architecture:

```text
React + TypeScript
       ↓
REST API
       ↓
Django REST Framework
       ↓
PostgreSQL
```

The frontend must not access PostgreSQL directly.

## 2. Frontend

Use:

- React
- TypeScript
- Vite
- Material UI
- React Router
- Axios
- TanStack Query
- React Hook Form
- Zod
- Day.js

The frontend should be modular and component-driven.

## 3. Backend

Use:

- Python
- Django
- Django REST Framework
- PostgreSQL
- JWT authentication
- CORS configuration
- Environment-based configuration

Backend business logic must remain on the backend.

## 4. Database

PostgreSQL is the only database for the application.

Do NOT configure an SQLite fallback.

If PostgreSQL is unavailable, fail clearly rather than silently switching databases.

## 5. API

Use versioned APIs:

```text
/api/v1/
```

Future versions can use:

```text
/api/v2/
```

API contracts should be documented.

## 6. Authentication

Use JWT authentication.

No public registration.

The backend is the authority for authentication and authorization.

## 7. Role authorization

Use role-based permissions.

Current roles:

```text
OWNER
STAFF
```

Backend APIs must enforce permissions.

## 8. Environment configuration

Do not hard-code:

- secret keys
- database passwords
- database host
- production URLs
- API keys
- notification provider credentials

Use `.env` / deployment environment configuration.

Provide `.env.example`.

## 9. Local deployment

Version 1 runs on one Windows PC.

The system should be structured so that local deployment is an environment/deployment concern, not a reason to couple application code to Windows-specific paths.

## 10. Cloud migration

Future cloud deployment should be possible by changing deployment configuration rather than rewriting business logic.

Avoid:

- local-only database assumptions
- hard-coded localhost dependencies in business logic
- direct filesystem dependencies that prevent cloud storage later

## 11. Data ownership

PostgreSQL is the source of truth for business data.

The frontend is a client.

Calculated dashboard/report data should come from backend queries/services.

## 12. Historical data

Historical order measurements, payment records, delivered orders, salary records, and important financial information must remain traceable.

Do not overwrite history merely to represent the latest state.

## 13. Business logic

Business rules belong primarily in backend/domain/service layers.

The frontend should handle:

- display
- interaction
- client validation
- user experience

The backend must repeat critical validation.

## 14. Reusability

Build reusable components and services.

Do not copy/paste similar CRUD logic across modules.

## 15. Error handling

Use consistent API error responses.

The frontend should translate errors into understandable user-facing messages.

Do not expose internal stack traces to users.

## 16. Auditability

Important changes should be auditable.

## 17. Backup

Because Version 1 is local, database backup/restore is a first-class operational concern.

## 18. Architecture rule

Do not introduce a technology simply because it is popular.

Every dependency should solve a real problem for this application.
