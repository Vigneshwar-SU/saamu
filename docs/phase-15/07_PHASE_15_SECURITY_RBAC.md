# Phase 15 — Security & RBAC Verification

## Verify

### Anonymous
- Protected frontend routes are blocked.
- Protected API endpoints return 401.

### OWNER
- Can view permitted operational/financial information.
- Cannot perform STAFF-only mutations.
- Cannot create expenses, payments, assignments, payroll mutations or other restricted records.

### STAFF
- Can perform permitted management actions.
- Cannot bypass backend authorization by manipulating frontend requests.

### Audit
- `recorded_by` and other server-controlled fields cannot be spoofed.
- Financial history cannot be silently altered through unsupported update/delete routes.
