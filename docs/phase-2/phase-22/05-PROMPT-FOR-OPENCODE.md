# Implementation Prompt — Payments Module Completion

You are working on the **Saamu Tailors Enterprise Tailoring Management System**.

The project owner is currently unwell and does not want to perform manual testing now. Continue the implementation workflow and complete the **Payments module** thoroughly. The owner will perform comprehensive manual verification later and report any changes.

## Critical Instructions
1. Inspect existing code before modifying it.
2. Earlier Payments/Billing work already exists. Do NOT rebuild correct functionality from scratch.
3. Reuse existing models, APIs, services, components, utilities, and design patterns.
4. Do not introduce unrelated changes.
5. Do not weaken validation or permissions to make tests pass.
6. Backend business rules must remain authoritative.
7. Do not claim manual verification is complete.

## Business Requirements
Payment types:
- ADVANCE
- PARTIAL
- FINAL
- REFUND

Rules:
- Order total comes authoritatively from order line items.
- Net paid is calculated server-side.
- Refunds reduce net paid.
- Outstanding is calculated server-side.
- OWNER = view-only.
- STAFF = payment management.
- Online payment gateways, GST, and double-entry accounting are out of scope.

## Workflow

### 1. Audit
Inspect:
- `apps/payments/`
- billing/invoice integration
- order models/services
- finance/income integration
- serializers
- views/viewsets
- URLs
- migrations
- frontend Payments page/components
- frontend payment API service/hooks
- tests
- relevant phase documentation

Determine exactly what is incomplete or incorrect.

### 2. Backend
Complete only what is required:
- payment creation
- required payment types
- payment methods
- server-side amount validation
- safe refunds
- authoritative totals
- net paid/outstanding calculations
- status consistency
- server-side RBAC
- meaningful API errors
- no unnecessary data destruction

### 3. Frontend
Complete the Payments module using the existing Saamu Tailors ERP design system:
- real API data
- payment records
- permitted payment operations
- required payment fields
- validation
- loading/empty/success/error states
- OWNER read-only behavior
- no fake static data where API data is expected

### 4. Integration
Ensure payment changes correctly propagate to:
- Orders
- Customers
- Invoices/Billing
- Income
- Dashboard financial summaries

Do not alter unrelated business logic.

### 5. Automated Verification
Run:
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py migrate --plan`
- relevant backend tests
- full backend tests if practical
- frontend TypeScript check
- frontend lint
- frontend production build

Fix failures caused by your implementation.

### 6. Final Review
Check:
- migrations
- imports/routes
- frontend/backend API contract
- OWNER/STAFF permissions
- refund calculations
- client input cannot override authoritative financial calculations
- existing features remain intact

## Deliverables
Report:
1. Implementation summary
2. Files changed
3. Migrations created/applied
4. Automated test results
5. Remaining implementation issues
6. Explicitly state: **Manual verification: PENDING — not performed.**

Do not proceed to Settings in this task. Stop after Payments is implementation-complete.
