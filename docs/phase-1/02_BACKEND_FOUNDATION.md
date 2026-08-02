# Backend Foundation

## Objective
Stabilize Django/DRF before business-domain implementation.

## Technology
- Python
- Django
- Django REST Framework
- PostgreSQL
- Environment-based configuration

Use the versions/constraints established by Phase 0.

## PostgreSQL Only
PostgreSQL is mandatory. No SQLite fallback, SQLite development DB, conditional switching, or automatic DB selection.

Environment variables:
```text
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD
DATABASE_HOST
DATABASE_PORT
```

Never hard-code credentials.

## Environment
`.env.example` must document, without real secrets:
```text
SECRET_KEY
DEBUG
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD
DATABASE_HOST
DATABASE_PORT
ALLOWED_HOSTS
TIME_ZONE
CORS_ALLOWED_ORIGINS
```

## DRF
Configure DRF centrally. Default permissions must not be `AllowAny`; use authenticated access as the secure default unless an endpoint is explicitly public.

Business role permissions belong to Phase 2.

## JWT
Ensure `djangorestframework-simplejwt` is available as the authentication foundation. Do not implement the complete login/token workflow unless only foundation correction is needed.

## API Versioning
All application APIs use:
```text
/api/v1/
```

Health endpoint:
```text
GET /api/v1/health/
```

Response:
```json
{
  "status": "ok",
  "application": "Saamu Tailors",
  "version": "1.0"
}
```

Do not create business endpoints.

## Errors
Establish a consistent DRF exception-handling foundation. A predictable structure should be used, e.g.:
```json
{
  "success": false,
  "error": {
    "code": "SOME_ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```
Do not expose credentials, stack traces, filesystem paths, or internal secrets.

## Pagination
Configure standard DRF pagination for future list endpoints. No business list APIs in this phase.

## CORS
Use environment-driven allowed origins. Do not use unrestricted wildcard production CORS.

## Logging
Establish INFO/WARNING/ERROR/CRITICAL logging. Never log passwords, JWT tokens, DB passwords, secrets, or unnecessary sensitive customer data.

## Static/Media
Keep STATIC_ROOT, STATIC_URL, MEDIA_ROOT and MEDIA_URL project-relative or environment-driven. Do not hard-code `D:\Projects\saamu\` or similar paths. Keep it compatible with future object storage.

## Scope
No business models or business endpoints.
