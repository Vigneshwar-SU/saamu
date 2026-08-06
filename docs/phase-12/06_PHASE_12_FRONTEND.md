# Phase 12 — Frontend Specification

## Expense Page
Provide expense list, summary, category, date, amount, payment method, recorded user and description where appropriate.

## Create Expense
STAFF gets an `Add Expense` action with:
- Category
- Amount
- Expense date
- Description
- Payment method

Use the existing form validation approach.

## Validation
Required fields, amount > 0, valid category/payment method and valid date. Backend remains authoritative.

## OWNER
View-only UI; no Staff mutation controls.

## Filters
Provide useful date range, category and payment-method filters.

## Summary
Show useful totals such as total expenses, expense count and current-period expenses based on backend data.

## States
Implement loading, error and empty states.

## Cache
Invalidate/refetch expense list and summary queries after mutations.
