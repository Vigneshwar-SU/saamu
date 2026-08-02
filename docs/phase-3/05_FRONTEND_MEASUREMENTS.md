# Frontend Measurement Management

Manage measurements from the customer context.

## Display
Clearly distinguish current measurement from history. Show garment type, values, unit, notes, and relevant dates.

## Create
STAFF only. Support:
- Shirt
- Pant

Render relevant structured fields. Do not use a generic uncontrolled JSON editor.

## Edit/History
Respect the backend history strategy. If measurements are versioned/immutable, editing must create a new current version rather than silently destroying history.

## OWNER
OWNER can view current measurements and history but cannot modify them.

## Validation
Provide clear client-side validation while keeping backend validation authoritative.

## Future Compatibility
Do not connect measurements directly to orders yet.
