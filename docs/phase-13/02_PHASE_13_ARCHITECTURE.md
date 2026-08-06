# Phase 13 — Architecture

Reuse the existing `backend/apps/finance/` ledger, Phase 11 billing/payment services, dashboard architecture, authentication/RBAC, and existing React finance patterns.

## Financial Flow
CustomerPayment → payment/refund classification → net customer receipts → income aggregation → Income UI/dashboard.

Expenses remain separate:
Expense → expense aggregation.

## Source of Truth
Actual customer payment records are authoritative for customer-derived income.

The frontend must never be the financial source of truth.

## Refunds
REFUND transactions reduce net customer income. Do not count a refund as positive income.

## Design Rule
Prefer one reusable server-side aggregation service for income API, summary and dashboard data. Avoid duplicate calculation logic.
