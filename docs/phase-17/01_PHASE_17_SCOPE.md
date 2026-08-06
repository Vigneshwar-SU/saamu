# Phase 17 — Scope

## Title
**Reports Export & Data Portability — Business Reporting Export**

## Objective
Extend the authoritative Phase 14 Reports module with safe, user-facing export functionality so Saamu Tailors can take business reports outside the application for review, sharing, printing, and future migration workflows.

## Primary deliverable
A Reports export capability for the existing Reports page and existing `GET /api/v1/reports/summary/` data model.

Support:
- CSV export.
- PDF export.
- The exact applied Reports date range.
- Server-authoritative totals using the Phase 14 reporting aggregation.
- OWNER + STAFF access.
- No new business calculations, financial records, or accounting behavior.

## Explicit non-goals
Do NOT implement:
- WhatsApp/SMS integration or automated reminders.
- Cloud deployment or cloud backup.
- Scheduled exports or email delivery.
- GST, accounting, payment gateway, or payroll behavior changes.
- New report metrics.
- Destructive database operations.
- Browser-triggered backup/restore.

## Phase boundary
Phase 17 is intentionally one feature: **Reports Export**.

WhatsApp/customer communication is a separate future phase so external-service credentials, privacy, retries, and failures can be designed independently.

## Success criteria
- CSV and PDF exports work from Reports.
- Date filtering is consistent.
- Export data matches authoritative report calculations.
- OWNER and STAFF can export; anonymous users cannot.
- Invalid ranges use the existing error contract.
- Export endpoints do not mutate data.
- Backend/frontend gates pass.
- Documentation is complete.
- Manual verification remains NOT STARTED until actually performed.
