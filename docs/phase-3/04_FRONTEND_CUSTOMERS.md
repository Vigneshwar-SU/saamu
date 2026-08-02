# Frontend Customer Management

Replace the Phase 1 customer placeholder with functional customer management using the existing MUI ERP design, API client, auth context, error handling, and reusable components.

## Customer List
Display useful fields such as:
- name
- mobile
- customer ID/code
- active status
- last updated information where useful

Provide search, pagination, active/archived filtering, loading, empty, and API error states.

## Create/Edit
STAFF only.

Validate name, mobile, optional fields, and sensible lengths. On success, provide useful feedback and refresh/navigate appropriately.

## Archive
STAFF only. Confirm before archiving/deactivation. Do not offer destructive permanent deletion as the normal UI.

## Detail
Show customer information, active/archived state, current measurements, and measurement history summary. Do not show future order information.

## OWNER
OWNER can list/search/view customers and measurements but must not see/use mutation controls.

## STAFF
STAFF can see Add Customer, Edit, Archive, Add Measurement, and Edit Measurement controls.

Frontend role checks are UX only; backend authorization remains authoritative.
