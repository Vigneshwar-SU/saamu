# Phase 14 — Frontend Specification

Build the reporting UI using the existing React + TypeScript + React Query architecture and Saamu Tailors ERP visual language.

## Reports Page
Provide a clear read-only business overview with appropriate sections for:
- Orders overview
- Order status distribution
- Customer activity
- Tailor workload
- Income
- Expenses
- Net position
- Payment/refund information
- Relevant trends/breakdowns

Do not add charts merely for decoration.

## Filters
Provide:
- From date
- To date
- Apply/reset behavior

Backend remains authoritative for filtered totals.

## UX
Include loading, empty, error states, clear labels, readable monetary values, and pagination where record-level tables are used.

## Permissions
OWNER and STAFF may view reports. No mutation buttons belong on Reports.

## Cache
Use React Query and invalidate/refetch report queries when underlying mutations require it.
