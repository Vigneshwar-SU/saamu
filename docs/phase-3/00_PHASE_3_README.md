# Saamu Tailors — Phase 3 README

## Phase
Phase 3 — Customer & Measurement Management

## Purpose
Build the first real business domain of Saamu Tailors: customer records and reusable tailoring measurements.

This phase integrates with the completed authentication foundation while remaining focused on customer and measurement data.

## Roles
Exactly two application roles remain:
- OWNER — view-only for business operations
- STAFF — operational management role

OWNER can view customers and measurements but cannot create, edit, or archive business records.

STAFF can create, view, edit, and archive customers and create/edit/view measurements.

## Scope
Implement:
- Customer model and API
- Customer search, pagination, detail, create, edit, archive
- Customer validation
- Measurement model and API
- Shirt and Pant measurement support
- Measurement history/versioning
- Customer-measurement relationship
- Backend role permissions
- Frontend customer management
- Frontend measurement management
- Tests and documentation

## Business Context
Customers bring their own cloth material to Saamu Tailors for stitching. Customer measurements are reusable for future stitching work.

Do not treat this as a ready-made clothing inventory system.

## Out of Scope
Do NOT implement:
- Orders
- Garments/order line items
- Cloth/material inventory
- Tailor assignment/workload
- Salary
- Income/expenses
- Payments
- Locker/collection workflow
- Digital bills
- WhatsApp/SMS
- Dashboard/reporting
- Notifications

## Completion
Create `docs/PHASE_3_COMPLETION_REPORT.md`.

After Phase 3 is complete, STOP. Do not start Phase 4 automatically.
