# Customer Requirements

## Customer Purpose
A customer is a person who brings cloth material to Saamu Tailors for stitching. The record must be reusable across multiple future orders.

## Minimum Information
Implement a practical model containing at least:
- customer ID
- full name
- mobile number
- alternate mobile number (optional)
- address (optional)
- notes (optional)
- active/archived status
- created timestamp
- updated timestamp

Follow existing project naming conventions.

## Mobile
Mobile number is important for future customer contact and digital bill/WhatsApp/SMS features. Validate it appropriately for the India-focused application without making the architecture unnecessarily country-specific.

Do not send messages in Phase 3.

## Duplicate Handling
Do not silently create duplicates based only on name. Use mobile/search assistance to help staff identify existing customers. Do not impose a simplistic unique-phone rule that breaks legitimate shared family numbers unless clearly justified.

## Search/List
Support search by:
- name
- mobile
- customer ID/code where applicable

Support pagination and active/archived filtering.

## Archive
Normal staff workflow should archive/deactivate rather than physically delete customers, preserving historical relationships.

## Permissions
OWNER:
- list/search/detail/view measurements
- no create/edit/archive

STAFF:
- create/view/edit/archive

## Audit-Friendly Fields
Preserve created_at and updated_at. Do not introduce a large audit framework in this phase.
