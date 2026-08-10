# Phase 22 — Implementation Prompt

You are implementing **Phase 22 — Settings** of the Saamu Tailors project.

## Before Coding
1. Audit the repository.
2. Inspect existing Settings-related code.
3. Inspect the existing `ShopDetails` model/API and billing implementation.
4. Inspect authentication and OWNER/STAFF permissions.
5. Inspect frontend routes, services, hooks, components, types and form/validation patterns.
6. Determine what is already implemented and what is genuinely missing.

## Core Rule
**Reuse existing authoritative functionality instead of creating duplicate models, endpoints, or sources of truth.**

If `ShopDetails` already provides the required shop configuration, build the Settings UI around it.

## Implement
Complete a real Settings module with:
- Shop/business information supported by the existing backend.
- Appropriate current-account information.
- Only meaningful supported application preferences.
- Correct OWNER/STAFF behavior.
- Server-authoritative authorization.
- Form validation.
- Loading, saving, success, empty and API-error states.
- Correct React Query cache invalidation/refetch.
- Accurate TypeScript API types.
- No hard-coded shop information where authoritative data exists.

## Security
Do NOT expose or allow editing of:
- Django secret key
- Database credentials
- JWT secrets
- Environment variables
- API secrets
- Deployment configuration
- Other sensitive infrastructure settings

## Backend
Keep changes minimal. Reuse existing models/services. Enforce permissions server-side. Add tests. Create migrations only if the schema genuinely changes.

## Frontend
Follow existing project conventions and reuse existing API client, React Query, form validation, UI and styling patterns. Do not add unnecessary dependencies.

## Verification
Run:
```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

Run the full backend test suite.

Run:
```text
npm run lint
npx tsc --noEmit
npm run build
```

Fix real failures. Do not weaken tests or bypass type checking/linting.

## Completion Report
Report:
1. Implementation status.
2. What already existed and was reused.
3. Backend changes.
4. Frontend changes.
5. API changes.
6. RBAC behavior.
7. Files changed.
8. Migration status.
9. Automated verification results.
10. Known limitations.
11. Manual verification status.

Manual verification must remain **PENDING** unless actually performed.

## Do Not
- Rebuild billing/shop details unnecessarily.
- Create duplicate sources of truth.
- Add speculative features.
- Expose secrets.
- Change unrelated modules.
- Claim manual verification was performed when it was not.
- Stop at a mockup; implement the working feature.
