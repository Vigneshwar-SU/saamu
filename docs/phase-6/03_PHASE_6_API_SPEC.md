# Phase 6 — API Specification

All endpoints use `/api/v1/`.

## Attendance
- `GET /attendance/` — OWNER + STAFF; filters: tailor, date_from, date_to, status, page.
- `POST /attendance/` — STAFF.
- `GET /attendance/{id}/` — OWNER + STAFF.
- `PATCH /attendance/{id}/` — STAFF.
- Optional bulk endpoint: `POST /attendance/bulk/` if implemented cleanly.

## Payroll
- `GET /payroll/periods/` — OWNER + STAFF.
- `POST /payroll/periods/` — STAFF.
- `GET /payroll/periods/{id}/` — OWNER + STAFF.
- `POST /payroll/periods/{id}/calculate/` — STAFF.
- `POST /payroll/periods/{id}/finalize/` — STAFF.
- `GET /payroll/entries/` — OWNER + STAFF; filters period/tailor.
- `GET /payroll/periods/{id}/tailors/{tailor_id}/` — OWNER + STAFF.

## RBAC
OWNER: reads only.
STAFF: all allowed mutations.
Anonymous: 401.

Continue the existing `{success:false,error:{code,message,details?}}` error contract.
