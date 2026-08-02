# Authentication Requirements

## User Model
Extend the existing custom User model carefully with:
```text
role
```

Allowed application roles:
```text
OWNER
STAFF
```

Do not create additional business roles.

## Login
Provide a SimpleJWT-based login endpoint. Invalid credentials must return a safe authentication error without revealing whether a username exists.

## Refresh
Provide a refresh-token endpoint using the existing SimpleJWT setup.

## Current User
Provide:
```text
GET /api/v1/auth/me/
```

Return only appropriate fields such as:
- id
- username
- role
- active status where appropriate

Never return passwords, hashes, or raw tokens.

## Logout
Implement a practical logout/token invalidation strategy compatible with SimpleJWT. If blacklist is used, configure and test it.

## Authentication State
Frontend must know:
- authenticated/not authenticated
- current user
- current role

## Token Configuration
Keep the SimpleJWT settings established in Phase 1 unless a documented reason requires a change.

## Boundary
Authentication is implemented here. Business-specific authorization is applied when business APIs are created later.
