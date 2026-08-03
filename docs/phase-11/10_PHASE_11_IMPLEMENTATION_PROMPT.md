# Phase 11 — Implementation Prompt

You are continuing development of the Saamu Tailors Tailoring Management System.

Phase 10 is complete and PASS. The next phase is Phase 11: Payments & Billing.

Before changing code:
1. Inspect the entire repository.
2. Read the existing Phase 11 documentation in `docs/phase-11/`.
3. Read `docs/ROADMAP.md`.
4. Review completed Phase 1–10 documentation and implementation.
5. Inspect existing order, customer, payment, settlement, payroll, authentication, RBAC, API, and frontend architecture.
6. Determine what already exists before creating anything new.

Implement ONLY the Phase 11 scope.

Phase 11 must deliver:
- customer payments
- ADVANCE / PARTIAL / FINAL / REFUND payment types
- order total
- total paid
- outstanding balance
- payment status
- digital bill containing shop, customer, order, garment, payment, and date details

Follow all Phase 11 scope, backend, API, frontend, RBAC, testing, manual-verification, and deferred-item documents.

Important:
- PostgreSQL only.
- Preserve completed phases.
- Do not duplicate Phase 7 settlement logic.
- Backend is authoritative for financial calculations and permissions.
- Do not implement PDF, WhatsApp/SMS, payment gateways, GST, double-entry accounting, or other later/deferred features.
- Do not claim manual verification was performed unless it actually was.

After implementation, produce a Phase 11 Completion Report containing:
1. Status
2. Scope
3. Implementation summary
4. Backend changes
5. Frontend changes
6. Database changes
7. API changes
8. RBAC
9. Testing results
10. Manual verification status
11. Documentation
12. Files changed
13. Known issues
14. Deferred items
15. Git verification
16. Phase 12 readiness
