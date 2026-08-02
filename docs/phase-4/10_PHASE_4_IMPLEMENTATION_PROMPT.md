# OpenCode Prompt — Saamu Tailors Phase 4

Implement **Phase 4 — Orders & Tailoring Workflow**.

Before coding, read every file in `docs/phase-4/`, especially:
- 01_PHASE_4_SCOPE.md
- 02_PHASE_4_BUSINESS_RULES.md
- 03_PHASE_4_DATA_MODEL.md
- 04_PHASE_4_API_SPEC.md
- 05_PHASE_4_FRONTEND_SPEC.md
- 06_PHASE_4_RBAC_AND_SECURITY.md
- 07_PHASE_4_TESTING_ACCEPTANCE.md
- 08_PHASE_4_GIT_WORKFLOW.md
- 09_PHASE_4_COMPLETION_REPORT_TEMPLATE.md

Also inspect the existing implementation and Phase 3 completion report.

## Critical rules
1. Do not redesign the architecture.
2. Do not implement Phase 5+ features.
3. Preserve completed Phase 3 behavior.
4. OWNER remains read-only; STAFF is the operational mutation role.
5. Backend authorization is authoritative.
6. Preserve historical measurement meaning for existing orders.
7. Do not physically delete orders.
8. Use PostgreSQL and existing API error handling.
9. Follow the current React/TypeScript/MUI/TanStack Query patterns.
10. Do not add unnecessary dependencies.
11. Never commit secrets.
12. Avoid nested page scrolling bugs.
13. Keep scope strictly to Phase 4.

## Work sequence

### 1. Inspect
Review Django apps, Customer/Measurement models and APIs, RBAC, auth, API client, routing/layout, UI patterns and tests.

### 2. Backend
Implement an Orders app with Order, OrderItem and preferably OrderStatusHistory; migrations; serializers; views/viewsets/actions; URLs; validation; RBAC; measurement snapshot/reference; lifecycle rules; standardized errors; admin where useful.

Do not mutate Phase 3 measurement history.

### 3. Tests
Test CRUD/read, lifecycle, invalid transitions, measurement snapshot/history, quantities/prices/dates, multiple garments, OWNER 403, STAFF mutations, anonymous access and regression.

### 4. Frontend
Replace Orders placeholder with list/search/filter/pagination, create order, detail, garment items, measurement selection, status workflow, STAFF mutation controls, OWNER view-only UI and proper loading/error/empty states.

### 5. Verify
Run backend and frontend checks. Start servers and test the real STAFF flow and OWNER flow. Verify measurement updates do not alter existing order history.

### 6. Documentation
Create/update `docs/PHASE_4_COMPLETION_REPORT.md` using the template. Record only real results.

### 7. Git
After verification:
- `git status`
- `git diff --stat`
- inspect relevant diff
- ensure no secrets/junk
- commit with a focused message
- push to configured remote
- record commit hash and push result
- show final `git status`

## Stop condition
Do not proceed to Phase 5. Stop after Phase 4 is implemented, tested, documented, committed and pushed.

If blocked, report the exact blocker, command/error, verified facts and safest next action. Never hide failures or mark them passed.
