# Phase 22 — Frontend Plan

## Settings Page
Create or complete the Settings page using existing project UI conventions.

## Sections
Use only sections justified by the backend/domain model:
1. Shop / Business Information
2. Current Account Information
3. Supported Application Preferences

## Form Behavior
- Load authoritative data.
- Populate existing values.
- Validate input.
- Show saving state and success feedback.
- Show API validation errors.
- Provide retry on loading failure.
- Protect unsaved changes where practical.

## RBAC
Frontend visibility should match permissions, but backend authorization remains the security boundary.

## Integration
After updates, invalidate/refetch relevant React Query caches and ensure other modules use the updated authoritative data.

## Code Quality
Reuse existing API clients, hooks, form validation, UI components and TypeScript conventions. Avoid unnecessary dependencies.
