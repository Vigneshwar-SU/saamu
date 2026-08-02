# Saamu Tailors — Phase 5 Scope

## Phase 5: Tailors, Workload & Piece-Rate Salary

### Objective
Build the tailoring workforce module required to manage tailors, assign order-item work, track workload, record completed pieces, and calculate piece-rate earnings.

### In Scope
- Tailor profile: name, optional mobile, notes, active/inactive state.
- Archive/restore; no physical deletion.
- Assign existing order items to active tailors.
- Support multiple assignments against one order item.
- Track assigned and completed quantities.
- Controlled work lifecycle: `ASSIGNED → IN_PROGRESS → COMPLETED`.
- Configurable piece rates.
- Historical rate snapshot on each work assignment.
- Tailor workload and earnings summaries with useful filters.
- Tailors list/detail, workload and earnings UI.
- OWNER = view-only; STAFF = operational mutations.
- Backend-authoritative RBAC.

### Explicitly Out of Scope
Attendance, payroll processing, salary transfers, tax/PF/ESI, leave management, notifications, WhatsApp/SMS, dashboard analytics, income/expense accounting, payments, billing/invoices, cloud deployment.

### Existing Foundations
Reuse Phase 2 authentication/RBAC, Phase 3 customers/measurements, Phase 4 orders/measurement snapshots, existing API error format, frontend architecture, MUI theme, layout, and role-aware patterns.

Do not redesign the architecture without a concrete requirement.
