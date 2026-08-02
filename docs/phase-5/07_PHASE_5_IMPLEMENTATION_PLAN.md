# Saamu Tailors — Phase 5 Implementation Plan

## Step 1 — Tailors Backend
Create `apps/tailors`, models, serializers, views, URLs, admin, migration, archive/restore, permissions and tests.

## Step 2 — Piece Rates
Implement configurable garment/work rates, Decimal validation, historical rate snapshots and tests.

## Step 3 — Work Assignments
Implement assignment APIs, transactional remaining-quantity validation, status lifecycle, historical records and tests.

## Step 4 — Earnings
Implement earnings calculations from completed work and historical rate snapshots, with filtered summaries and tests.

## Step 5 — Frontend
Add types/services/hooks, replace Tailors placeholder, add detail, workload/assignment UI, earnings UI, and role-aware controls.

## Step 6 — Integration
Run backend/frontend and execute STAFF + OWNER manual workflows and regression checks.

## Step 7 — Documentation
Create `docs/phase-5/PHASE_5_COMPLETION_REPORT.md` containing implementation, model, APIs, RBAC, tests, manual verification, known issues, deferred items, changed files, Git verification, and Phase 6 readiness.

## Step 8 — Git
Do not automatically begin Phase 6.

After implementation:
1. Run verification.
2. Produce completion report.
3. Stop for human review.
4. After approval, commit Phase 5.
5. Push to `origin/master`.
6. Verify local and remote commit match.
7. Only then proceed to Phase 6.
