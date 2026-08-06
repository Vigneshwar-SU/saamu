# Phase 12 — Architecture

Follow the existing Saamu Tailors architecture: Django + DRF + PostgreSQL backend and React + TypeScript frontend.

## Backend
Prefer a dedicated `backend/apps/expenses/` module following existing conventions:
- models.py
- serializers.py
- views.py
- urls.py
- admin.py
- services.py
- tests/

## Frontend
Use the existing pages/components/hooks/services/types patterns.

## Data Flow
STAFF → React Expense Form → REST API → serializer validation → service → PostgreSQL.

PostgreSQL → API → serializer → existing data layer → React UI.

## Authorization
OWNER: GET allowed, mutations denied.
STAFF: GET and allowed management mutations.
Anonymous: 401.

## Financial Calculation
Expense totals are derived from database records. Do not duplicate aggregation logic.

Do not modify Phase 11 billing/payment behavior or finalized payroll logic unless strictly necessary and documented.
