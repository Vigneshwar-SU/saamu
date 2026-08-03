# Phase 10 — Deferred Items & Guardrails

## Deferred
- Tax/PF/ESI.
- Leave deductions.
- Attendance monetary penalties/bonuses.
- Salary slips/PDFs.
- WhatsApp/SMS salary notifications.
- Bank/payment gateway integration.
- Double-entry accounting.
- GST.
- Automatic income/expense creation.
- Bulk settlement redesign.
- Payroll changes after finalization.

## Guardrails
1. Never rewrite finalized payroll.
2. Never delete historical salary, advance, payment, or payroll records.
3. Never allow negative payable amounts.
4. Never allow overpayment.
5. Never trust client-supplied audit fields.
6. Preserve Phase 7 concurrency locks.
7. Preserve historical rate/configuration snapshots.
8. Do not duplicate existing payment/advance logic.
9. Keep OWNER read-only.
10. Keep financial calculations Decimal-based.
