# Saamu Tailors — Phase 2 README

## Phase
Phase 2 — Authentication & Role-Based Access Control

## Purpose
Implement the real authentication system that Phase 1 intentionally deferred.

Phase 1 already established Django/DRF, PostgreSQL-only configuration, the custom User foundation, SimpleJWT dependency, secure default permissions, centralized API client, token-service foundation, standardized errors, and testing.

Phase 2 now turns those foundations into working authentication and authorization.

## Roles
Exactly two application roles exist:

- `OWNER` — view-only business user
- `STAFF` — operational management user

OWNER can log in and view permitted information, but must not create, edit, or delete business records.

STAFF can log in and perform operational management actions once business features exist.

## Scope
Implement:
- User role field and choices
- Login
- Access and refresh tokens
- Logout/invalidation
- Current-user (`me`) endpoint
- Central frontend auth state
- Protected routes
- Real frontend login
- Token persistence
- Refresh handling
- Role-aware frontend foundation
- Backend role permissions
- Authentication and authorization tests
- Documentation

## Out of Scope
Do not implement customers, measurements, orders, garments, tailors, workload, salary, payments, income, expenses, lockers, collection workflow, bills, WhatsApp/SMS, business dashboard/report logic, or notifications.

## Critical Rule
Backend authorization is authoritative. Frontend hiding is UX only.

## Completion
Create a Phase 2 completion report and STOP. Do not begin Phase 3 automatically.
