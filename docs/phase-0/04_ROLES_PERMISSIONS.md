# Saamu Tailors — Roles & Permissions

## Version 1 roles

There are exactly two application roles:

1. OWNER
2. STAFF

Do not create additional business roles in Version 1 unless explicitly approved.

## 1. Owner

Owner is a full-access role.

### Owner can

- View dashboard.
- View customers.
- Create/edit customers.
- View customer history.
- Manage orders.
- Manage measurements.
- Manage cutting workflow.
- Manage tailor assignments.
- Manage tailors.
- Manage salary records.
- Manage payments.
- Generate bills.
- Manage expenses.
- View income.
- View reports.
- Manage shop settings.
- Create/manage staff accounts.
- Enable/disable staff accounts.
- Reset staff credentials where supported.
- View audit/activity information.

Owner is NOT view-only.

The owner actively participates in shop operations.

## 2. Staff

Staff is the daily operational role.

### Staff can

- View/search customers.
- Create/edit customers.
- Create/manage orders.
- Record measurements.
- Update operational statuses.
- Manage cutting-related workflow as permitted.
- Assign/update tailor work as permitted.
- View tailor workload.
- Record customer payments.
- Generate bills.
- Record expenses.
- View relevant income/payment information.
- Manage customer delivery/collection.
- Use normal daily shop functions.

### Staff cannot

- Create another owner.
- Change owner permissions.
- Delete/disable the owner.
- Manage system-level security settings.
- Perform owner-only staff administration.

The exact permission matrix should be enforced at the backend API level, not only hidden in the frontend.

## Authentication rules

- No public registration.
- Owner creates staff accounts.
- Passwords must be securely hashed.
- Authentication uses JWT.
- Protected APIs must enforce role permissions.
- Frontend route restrictions are supplemental; backend authorization is authoritative.

## Future extensibility

The permission system should be designed so additional roles can be introduced later without rewriting existing authorization architecture.
