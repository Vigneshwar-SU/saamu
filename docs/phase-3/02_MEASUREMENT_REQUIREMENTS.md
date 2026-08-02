# Measurement Requirements

## Purpose
Measurements are customer-specific tailoring measurements reusable for future stitching. They are NOT orders.

## Garment Types
At minimum support:
- Shirt
- Pant

Use a clean extensible structure. Do not invent dozens of arbitrary fields without a clear tailoring reason.

A measurement record should support:
- customer
- garment type
- structured measurement values
- notes
- created timestamp
- updated timestamp

## Units
Use one consistent first-version unit, preferably inches, and document it. Store numeric values as decimal numbers where practical, not free-form text.

## History
Do not destroy historical measurements when measurements change.

The design must preserve previous records and make the newest applicable measurement identifiable, using versioning or immutable records plus a current marker.

## Permissions
STAFF can create and modify measurements.
OWNER can view current measurements and history but cannot modify them.

## Future Compatibility
Measurements must remain reusable by future Order/Garment phases without coupling them directly to an order.

Do not implement Orders in Phase 3.
