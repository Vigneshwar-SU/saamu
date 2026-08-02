# Backend Authentication API

## Base
```text
/api/v1/auth/
```

## Login
```text
POST /api/v1/auth/login/
```

Conceptual input:
```json
{
  "username": "example",
  "password": "example"
}
```

Conceptual success:
```json
{
  "access": "...",
  "refresh": "...",
  "user": {
    "id": 1,
    "username": "example",
    "role": "STAFF"
  }
}
```

Do not expose sensitive fields.

## Refresh
```text
POST /api/v1/auth/refresh/
```

## Current User
```text
GET /api/v1/auth/me/
```
Requires authentication.

## Logout
```text
POST /api/v1/auth/logout/
```
Requires authentication and invalidates refresh authentication according to the selected strategy.

## HTTP Semantics
Use appropriate status codes:
- 200 success
- 400 malformed input
- 401 invalid/missing authentication
- 403 authenticated but forbidden

## Errors
Keep the Phase 1 standardized error contract:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

## Implementation
Use serializers for request/response validation. Keep views thin.

Login and refresh must be intentionally public entry points; `/me/` and logout require authentication.

## Testing
Every endpoint must have success and important failure coverage.
