# Phase 10 — API Specification

All endpoints are under `/api/v1/`.

## Salary configurations

### GET /salary-configurations/
OWNER + STAFF. List configurations with optional tailor, salary_model, and is_active filters.

### POST /salary-configurations/
STAFF only. Create a salary configuration.

### GET /salary-configurations/{id}/
OWNER + STAFF. Read configuration details.

### PATCH /salary-configurations/{id}/
STAFF only. Modify only records safely editable without changing finalized history. Prefer a new effective configuration for historical safety.

## Existing payroll endpoints
Keep these authoritative:
- `GET /payroll/periods/`
- `POST /payroll/periods/{id}/calculate/`
- `POST /payroll/periods/{id}/finalize/`
- `GET /payroll/periods/{id}/tailors/{tailor_id}/`
- Existing Phase 7 settlement/payment endpoints.

Enhance responses with salary-model and salary-component information.

## Optional dedicated breakdown
`GET /payroll/periods/{id}/tailors/{tailor_id}/salary-breakdown/`

Return salary model, fixed salary, completed pieces, piece-rate earnings, gross salary, advance deductions, payments, pending amount, settlement status, and attendance summary.

Use the existing standard `{success:false,error:{code,message,details?}}` contract.
