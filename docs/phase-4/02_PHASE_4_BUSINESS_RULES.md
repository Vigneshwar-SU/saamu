# Saamu Tailors — Phase 4 Business Rules

## Roles
OWNER is view-only for business operations. STAFF has operational mutation access. Backend enforcement is authoritative.

## Order
Every order has a stable database ID and a unique human-friendly order number. Every order belongs to exactly one existing customer.

## Garments
Current types: SHIRT and PANT. An order can contain one or more items. Each item has garment type, positive quantity, measurement version/snapshot, optional notes and pricing.

## Measurement snapshot
When an order is created, preserve the exact measurement version used. Later customer measurement changes must not alter historical order meaning. Missing required measurements must produce a clear validation error.

## Status lifecycle
Use:
- NEW — order received / cloth accepted
- CUTTING — cloth is being cut/prepared
- STITCHING — tailoring work is underway
- READY — finished and ready for collection
- COLLECTED — customer received finished clothes
- CANCELLED — order cancelled

CANCELLED and COLLECTED are terminal. Backend must reject invalid transitions.

## Dates
Order date defaults to current local date/time. Expected delivery is optional unless implementation makes it required. Delivery cannot precede order date. Record collection timestamp when status becomes COLLECTED.

## Money
Use Decimal fields, never floating-point values. Do not implement payment accounting in this phase.

## Deletion
Do not physically delete orders. Retain history and use cancellation.

## Auditability
Keep created/updated timestamps and preferably a small status-transition history without over-engineering a full audit system.
