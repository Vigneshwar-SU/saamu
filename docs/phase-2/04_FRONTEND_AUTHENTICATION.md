# Frontend Authentication

## Login Flow
```text
Login page
    |
    v
POST /auth/login/
    |
    v
Store auth state
    |
    v
Authenticated ERP layout
```

## Auth State
Expose at least:
```text
isAuthenticated
isLoading
user
role
login()
logout()
```

Use the existing frontend context architecture.

## Tokens
Use the Phase 1 token service. Do not scatter token handling across components.

Central Axios client attaches:
```text
Authorization: Bearer <access-token>
```

## Refresh
When access expires, attempt refresh appropriately. Avoid infinite loops.

If refresh fails:
1. clear tokens
2. clear auth state
3. redirect to Login

## Logout
Logout should:
1. call backend logout when possible
2. clear local tokens
3. clear user state
4. return to Login

Even if the network call fails, explicit logout must clear local credentials.

## Protected Routes
Unauthenticated users must be redirected to Login.

## Login Page
Connect the existing Login page to the real API and retain:
- existing design
- username/password
- show/hide password
- validation
- loading state
- errors
- responsive layout

Remove mock navigation.

## Roles
Understand `OWNER` and `STAFF`. Use role-aware navigation where useful. Do not implement business pages just to demonstrate it.

## UX
Handle loading, invalid credentials, expired sessions, network errors, server errors, and logout using Phase 1 error utilities.
