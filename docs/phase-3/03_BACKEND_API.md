# Backend Customer & Measurement API

Continue using `/api/v1/` and the standardized Phase 1/2 API error contract.

## Customers
Use an appropriate REST API under `/api/v1/customers/`.

Required capabilities:
- `GET /api/v1/customers/` — list, pagination, search, active/archived filtering
- `POST /api/v1/customers/` — STAFF only
- `GET /api/v1/customers/{id}/` — OWNER and STAFF
- `PATCH /api/v1/customers/{id}/` — STAFF only
- safe archive/deactivation operation — STAFF only

Do not physically delete customer records as the normal business workflow.

## Measurements
Use a simple scalable design, for example:
- `/api/v1/customers/{customer_id}/measurements/`
- `/api/v1/measurements/{id}/`

Required capabilities:
- list customer measurements
- create measurement
- view measurement
- update according to the selected history/versioning strategy

STAFF can create/modify. OWNER can view only.

## Validation
Backend must validate:
- required fields
- sensible phone format
- supported garment types
- valid decimal measurement values/ranges
- valid customer references

Frontend validation is not a security boundary.

## Permissions
Use authenticated database user roles. Never trust role values from React.

## Query Quality
Use appropriate indexes/select_related/prefetch_related where clearly useful. Avoid premature optimization.

## Tests
Cover anonymous access, OWNER read/mutation denial, STAFF CRUD permissions, validation, pagination, search, archive, measurement history, and customer-measurement relationships.
