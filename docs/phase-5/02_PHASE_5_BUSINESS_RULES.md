# Saamu Tailors — Phase 5 Business Rules

## Tailors
- Name is required.
- Mobile is optional.
- Tailors can be archived/restored.
- Archived tailors cannot receive new assignments.
- Historical assignments remain visible after archival.
- No physical deletion.

## Work Assignment
An assignment connects `Tailor → Order Item → Assigned Quantity`.

Rules:
- Only active tailors may receive new work.
- Order item must exist and belong to the selected order.
- Assigned quantity must be > 0.
- Assigned quantity cannot exceed the order item's currently unassigned quantity.
- Multiple assignments may consume one order item's quantity.
- Historical assignments must remain intact.
- Preserve creator/timestamps where appropriate.

## Work Status
`ASSIGNED → IN_PROGRESS → COMPLETED`

- ASSIGNED = work given to tailor.
- IN_PROGRESS = work started.
- COMPLETED = assigned work completed.
- Completed quantity cannot exceed assigned quantity.
- Completed work contributes to piece-rate earnings.
- Backend validates all transitions.

## Piece Rate
Rates are configurable by garment/work type and must use Decimal.

`earned_amount = completed_quantity × rate_snapshot`

The applicable rate is copied to the assignment so future rate changes never alter historical earnings.

## Salary
Phase 5 salary means piece-rate earnings, not fixed monthly payroll.

`Total Earned = Σ(completed quantity × historical rate snapshot)`

Provide completed pieces, earnings, garment/work-type breakdown, and date filtering. Do not implement payment settlement.

## Order Integrity
Do not mutate Phase 4 order totals, quantities, measurement snapshots, or historical status records.

## Roles
OWNER: read-only tailors, assignments, workload and earnings.
STAFF: full operational workforce management.
Backend permissions are authoritative.
