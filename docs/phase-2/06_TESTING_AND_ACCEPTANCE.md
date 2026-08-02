# Phase 2 Testing and Acceptance

## Backend Tests

Cover:

### Roles
- OWNER can be assigned
- STAFF can be assigned
- invalid roles are rejected

### Login
- valid OWNER login succeeds
- valid STAFF login succeeds
- invalid credentials fail safely
- invalid login does not reveal account existence

### Tokens
- access token works
- invalid access token is rejected
- refresh creates a valid access token
- invalid refresh token is rejected

### Me
- authenticated user can access `/auth/me/`
- anonymous user cannot
- role is returned
- sensitive fields are absent

### Logout
- logout succeeds
- invalidated refresh token fails if blacklist/invalidation is used

### Permissions
- anonymous denied
- OWNER recognized
- STAFF recognized
- OWNER cannot perform protected mutation operations
- STAFF receives staff authorization

Do not create fake business CRUD solely for testing.

## Frontend
Run:
```text
npm run lint
npx tsc --noEmit
npm run build
```

Manual verification:
1. Invalid login shows useful error.
2. OWNER login works.
3. STAFF login works.
4. Browser refresh behaves correctly.
5. Expired access token refreshes or logs out as designed.
6. Logout clears session.
7. Protected routes redirect anonymous users.
8. Role state matches `/me/`.

## Integration
Run backend and frontend simultaneously and verify:
```text
Frontend -> POST /api/v1/auth/login/ -> Django -> JWT -> authenticated frontend state
```

Then verify a protected request through the centralized frontend API client.

## Reporting
Every verification item must be marked:
```text
PASS
FAIL
BLOCKED
```
Never claim unexecuted tests passed.
