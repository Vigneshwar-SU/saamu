# Phase 12 — RBAC

## OWNER
Allowed: view expense list, details, summaries and filters.
Denied: create, modify, delete or other mutations.

## STAFF
Allowed: view and manage expenses according to implemented mutation rules.

## Anonymous
All protected requests return 401.

## Backend Authority
Frontend restrictions are not security. Every mutation must be backend-protected.

## recorded_by
Always use `request.user`. Never trust client `recorded_by`, `user_id` or `created_by`.

## Required Tests
- Anonymous list → 401
- Anonymous create → 401
- OWNER list → 200
- OWNER create → 403
- STAFF list → 200
- STAFF create → 201
- recorded_by spoofing rejected/ignored
