# Role-Based Access Control

## Roles
Only:
```text
OWNER
STAFF
```

## Authorization Matrix

| Capability | OWNER | STAFF |
|---|---:|---:|
| Login | Yes | Yes |
| View authenticated application | Yes | Yes |
| View business information | Yes | Yes |
| Create business records | No | Yes |
| Edit business records | No | Yes |
| Delete business records | No | Yes |
| Operational management | No | Yes |

## Backend
Create reusable DRF role permission classes/helpers.

Support concepts equivalent to:
```text
IsAuthenticated
IsOwner
IsStaffRole
IsOwnerOrStaff
```

Do not confuse application role `STAFF` with Django's built-in `is_staff` flag.

The application role must come from the custom User model.

## OWNER
OWNER is view-only for business operations.

## STAFF
STAFF is the operational management role.

## Scope
Do not create fake business CRUD merely to demonstrate permissions. Establish reusable authorization and test it.

## Frontend
Frontend may use role for navigation visibility and UX, but backend enforcement is mandatory.

## Superuser
A Django superuser must not silently become a third application role. Document how superusers are handled while application role remains OWNER or STAFF.

## Tests
Test anonymous denial, OWNER recognition, STAFF recognition, OWNER mutation denial where protected mutation permissions are exercised, and STAFF authorization.
