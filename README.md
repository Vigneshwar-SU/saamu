# Saamu Tailors — Tailoring Management System

A custom tailoring management system for **Saamu Tailors**, a family tailoring business operating since 1954.

The application digitizes the shop's operations: customer records, orders, measurements, tailoring workflow, tailor workload, payments, income, expenses, digital bills, and delivery/collection tracking.

**Current stage:** Phase 18 (Customer Communication & WhatsApp-Ready Delivery). Adds a read-only preparation endpoint `GET /api/v1/communications/messages/prepare/order/<id>/?message_type=...` (OWNER/STAFF) that returns a server-authored plain-text WhatsApp-ready message for one of four templates (order acknowledgement, order status update, ready for collection, payment/balance summary) plus a normalized phone destination and a fixed `wa.me` handoff URL — nothing is ever sent automatically. The Order Detail page gains a reusable Customer Communication panel with message-type selection, a compact preview, Copy WhatsApp Message (with copy-success state) and Open WhatsApp (disabled when no usable number), with loading/error/retry and duplicate-action protection. No provider integration, no credentials, no schema changes. Manual verification checklist pending.

---

## 1. Architecture

```text
React + TypeScript (Vite, Material UI)
        │
        │ REST API (/api/v1/)
        ↓
Django REST Framework
        ↓
PostgreSQL
```

- **Frontend:** React 19, TypeScript, Vite, Material UI, TanStack Query, React Hook Form, Zod, Day.js
- **Backend:** Django 5, Django REST Framework, SimpleJWT (JWT auth), PostgreSQL
- **Database:** PostgreSQL only (no SQLite fallback)
- **Deployment:** Local Windows PC in the shop (cloud-migration ready)

---

## 2. Requirements

- Python 3.12+
- Node.js 22+ and npm 10+
- PostgreSQL 16+ (installed and running as a service)

---

## 3. Backend Setup

From the project root:

```powershell
cd backend

# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements-dev.txt   # runtime + development (tests, black, isort)
# or: pip install -r requirements.txt  # runtime only

# 3. Configure environment
copy .env.example .env
# Edit .env with your PostgreSQL credentials and SECRET_KEY

# 4. Create the PostgreSQL database (one time)
psql -U postgres -c "CREATE DATABASE saamu_db;"

# 5. Verify configuration
python manage.py check

# 6. Apply migrations (initial foundation schema)
python manage.py migrate

# 7. Start the development server
python manage.py runserver 8000
```

Health check: `GET http://127.0.0.1:8000/api/v1/health/`

---

## 4. Frontend Setup

From the project root:

```powershell
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment
copy .env.example .env
# VITE_API_BASE_URL defaults to http://localhost:8000/api/v1

# 3. Start the development server
npm run dev
```

The frontend runs at `http://localhost:5173` and proxies `/api` to the backend on port 8000.

---

## 5. Running Locally

Run both processes in separate terminals:

| Process | Command | URL |
|---|---|---|
| Backend | `cd backend; .\.venv\Scripts\activate; python manage.py runserver` | http://127.0.0.1:8000 |
| Frontend | `cd frontend; npm run dev` | http://localhost:5173 |

Verify the frontend can reach the backend:

```text
GET http://localhost:5173/api/v1/health/
```

Expected response:

```json
{
  "status": "ok",
  "application": "Saamu Tailors",
  "version": "1.0",
  "database": "ok"
}
```

---

## 6. Authentication & Roles

### Application roles

Exactly two application roles exist. These are application roles and are independent of Django's `is_staff` / `is_superuser` flags.

| Role | Description |
|---|---|
| `OWNER` | View-only for business operations. Can log in and view permitted information but must not create, edit, or delete business records. |
| `STAFF` | Operational management user. Will create/edit/delete business records when business APIs exist. |

Django superusers keep `is_superuser`/`is_staff` for Django admin access; the application role is still exactly `OWNER` or `STAFF` (never a third role). Backend authorization reads the authenticated database user's `role` — a role supplied by the frontend is never trusted.

### Authentication endpoints

All under the versioned API:

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/login/` | public | Validate credentials, return access + refresh tokens and user info |
| POST | `/api/v1/auth/refresh/` | public (needs refresh token) | Exchange a valid refresh token for a new access token |
| GET | `/api/v1/auth/me/` | authenticated | Return the current user (`id`, `username`, `role`, `is_active`) |
| POST | `/api/v1/auth/logout/` | authenticated | Blacklist the supplied refresh token |

Login request:

```json
{ "username": "owner", "password": "..." }
```

Login response (passwords/hashes are never returned):

```json
{
  "access": "...",
  "refresh": "...",
  "user": { "id": 1, "username": "owner", "role": "OWNER", "is_active": true }
}
```

### JWT behavior

- Access tokens: 60 minutes (default). Sent as `Authorization: Bearer <access-token>`.
- Refresh tokens: 1 day (default). Not rotated.
- On a `401`, the frontend attempts a single refresh via `/auth/refresh/` and retries the original request. If refresh fails, tokens are cleared and the user is redirected to login.
- Logout blacklists the refresh token server-side, so a logged-out refresh token cannot be reused.

### Local development authentication setup

There is no public registration. Create the initial owner and staff accounts:

```powershell
cd backend
# Initial OWNER (reads OWNER_USERNAME/OWNER_PASSWORD env vars, defaults: owner)
python manage.py create_owner --username owner --password "Owner@12345" --superuser

# A STAFF operational user (via Django shell)
python manage.py shell -c "from apps.authentication.models import User, Role; User.objects.create_user(username='staff', password='Staff@12345', role=Role.STAFF)"
```

`create_owner` promotes an existing account to `OWNER` if it already exists and sets `--superuser` only when requested.

### Token storage (frontend)

Tokens are stored in browser storage via the centralized `authToken` service:
- **Remember Me checked** → `localStorage` (persists across browser restarts).
- **Remember Me unchecked** → `sessionStorage` (cleared when the browser session ends).

Tokens are never rendered as raw HTML or logged. The access token is short-lived; the refresh token is blacklisted on logout. Browser storage is readable by same-origin scripts (an XSS risk) — this is accepted for the single-PC local deployment and mitigated by the points above.

---

## 7. Customers & Measurements

### Customers

- List: `GET /api/v1/customers/?search=&status=active|archived|all&page=` (20 per page). Detail: `GET /api/v1/customers/{id}/`.
- **STAFF** can `POST /api/v1/customers/` (create), `PATCH /api/v1/customers/{id}/` (edit), and `POST /api/v1/customers/{id}/archive/` / `.../restore/`. **OWNER is view-only** — enforced by the backend.
- Search matches name / primary mobile / alternate mobile (case-insensitive) and a numeric search also matches the customer ID.
- Archived customers are retained and restorable; there is no physical delete. `is_active` is read-only via PATCH and only changed by the explicit archive/restore actions.
- Mobile numbers: 10–15 digits with an optional leading `+`. The alternate mobile must differ from the primary (shared/family numbers are allowed, so mobiles are not globally unique).
- There is no human-friendly customer code; the stable internal `id` is the identifier (documented decision).

### Measurements

- Recorded per customer and garment type (`SHIRT` / `PANT`); every numeric value is in **inches**.
- `GET/POST /api/v1/customers/{customer_id}/measurements/` (`?current=true` returns only the current rows) and `GET/PATCH /api/v1/measurements/{id}/` (PATCH reads any version and creates a new current one).
- Every save creates an immutable new version and marks it current; previous versions are preserved as history. `version` and `is_current` are read-only, and a garment type cannot be changed after creation.
- Shirt required: neck / chest / waist rounds, shoulder width, sleeve length, shirt length (sleeve & cuff rounds optional). Pant required: waist / hip rounds, length (thigh / knee / bottom rounds optional). Values must be 0.1–300.0; fields that do not belong to the selected garment are rejected.
- Frontend UI: `Customers` list (search / status filter / pagination, STAFF create/edit/archive/restore) and a detail page with the current measurement, version history, and per-garment entry forms.

---

## 8. Tailors, Workload & Piece-Rate Salary

### Tailors

- List: `GET /api/v1/tailors/?search=&scope=active|archived|all&page=` (20 per page). Detail: `GET /api/v1/tailors/{id}/`.
- **STAFF** can `POST /api/v1/tailors/` (create), `PATCH /api/v1/tailors/{id}/` (edit), and `POST /api/v1/tailors/{id}/archive/` / `.../restore/`. **OWNER is view-only** — enforced by the backend.
- Search matches name and mobile (case-insensitive). Archived tailors are retained and restorable; there is no physical delete. `is_active` is read-only via PATCH and only changed by the explicit archive/restore actions.
- Tailor `name` is required; `mobile_number` (10–15 digits, optional leading `+`) and `notes` are optional.

### Piece rates

- `GET/POST /api/v1/piece-rates/` and `PATCH /api/v1/piece-rates/{id}/` (rate or active flag only — no delete). `garment_type` is unique; `rate_per_piece` is a non-negative decimal.
- `STAFF` only for mutations; OWNER can view. Inactive rates cannot be used for new assignments.

### Work assignments & earnings

- `GET/POST /api/v1/work-assignments/`, detail `GET/PATCH /api/v1/work-assignments/{id}/` (PATCH updates `completed_quantity` only), and `POST /api/v1/work-assignments/{id}/status/` for status transitions.
- Lifecycle `ASSIGNED → IN_PROGRESS → COMPLETED` is backend-enforced; `COMPLETED` is terminal. `earned_amount = completed_quantity × rate_per_piece_snapshot`; the rate is snapshotted at assignment time and never altered by later rate edits.
- An assignment requires an active tailor and an order item with enough remaining quantity (validated under a row lock); the item's `assigned_quantity` / `remaining_quantity` are exposed on orders.
- Filters: `tailor`, `order`, `garment_type`, `status`, `date_from`, `date_to`.
- Earnings: `GET /api/v1/tailors/{id}/earnings/` (per-garment breakdown) and `GET /api/v1/tailor-earnings/summary/` (aggregate across tailors, incl. `outstanding_quantity`).
- Frontend: Tailors list (search / scope filter / pagination / earnings summary + piece-rate manager), Tailor detail (profile, earnings by garment, work assignments with progress + status actions, assign-work dialog).

## 8.1 Attendance & Payroll

- Attendance: `GET/POST /api/v1/attendance/`, detail `GET/PATCH /api/v1/attendance/{id}/`; statuses `PRESENT` / `ABSENT` / `HALF_DAY`, unique per `(tailor, attendance_date)`, filters `tailor`, `date_from`, `date_to`, `status`. Mutations are STAFF-only; records are never deleted.
- Payroll periods: `GET/POST /api/v1/payroll/periods/`, detail `GET /api/v1/payroll/periods/{id}/`, with aggregates (`total_completed_pieces`, `total_piece_rate_earnings`, `total_attendance_amount`, `total_payable`, `entry_count`).
- Lifecycle `DRAFT → CALCULATED → FINALIZED`: `POST .../calculate/` generates per-tailor entries from completed assignments (inclusive `completed_at` boundaries) using the immutable `rate_per_piece_snapshot` (`earnings = completed_quantity × snapshot`); in-progress/outstanding pieces contribute zero. `POST .../finalize/` locks the period (immutable; recalculation rejected).
- Attendance days are aggregated per tailor (`present_days` / `half_days` / `absent_days`); missing attendance is never counted as PRESENT. `attendance_amount` remains `0` until a monetary attendance rule is configured.
- Entries: `GET /api/v1/payroll/entries/` (`period`, `tailor` filters); per-tailor breakdown `GET /api/v1/payroll/periods/{id}/tailors/{tailor_id}/` (order, garment, assigned/completed/remaining, rate snapshot, earned).
- Frontend: Attendance page (filters + mark/edit), Payroll page (period list + calculate/finalize), Payroll detail (summary, tailor entries, per-tailor assignment breakdown). Mutation controls are hidden for OWNER.

## 8.2 Salary Payments, Advances & Settlement

- **Salary advances**: `GET/POST /api/v1/advances/`, detail `GET /api/v1/advances/{id}/`; filters `tailor`, `status` (`OUTSTANDING` / `DEDUCTED`), `date_from`, `date_to`. Create is STAFF-only and records `recorded_by`. Advances are never deleted or edited; a deduction records the `payroll_entry` and `deducted_at` on the advance.
- **Settlement is derived, never stored**: for each payroll entry, `gross_payable` = immutable `total_payable`, `advance_deductions` = sum of linked `DEDUCTED` advances, `payments_recorded` = sum of linked payments, and `outstanding_payable` = gross − deductions − paid. Settlement status is `UNPAID` / `PARTIALLY_PAID` / `SETTLED`. The payroll period list/detail, entry list, and `GET /payroll/entries/{id}/settlement/` all expose this summary.
- **Mutations (STAFF-only, FINALIZED periods only)**:
  - `POST /api/v1/payroll/entries/{id}/payments/` — record a payment (amount, date, method `CASH` / `BANK_TRANSFER` / `UPI` / `OTHER`, reference, notes). Overpayment is rejected.
  - `POST /api/v1/payroll/entries/{id}/apply-advance/` — deduct an `OUTSTANDING` advance of the same tailor against the entry (once only, never below zero).
  - `POST /api/v1/payroll/entries/{id}/settle/` — record one final payment for the full outstanding amount. `GET /api/v1/payroll/entries/{id}/payments/` returns the payment history.
- **Concurrency safety**: every settlement mutation runs in `transaction.atomic()` with `select_for_update()` row locks, so concurrent payments/advance applications can never overpay a single entry.
- Frontend: Advances page (tailor/status/date filters, pagination, STAFF-only Add Advance), Payroll list now shows paid / outstanding / settlement status per period, and Payroll detail gains a settlement panel per tailor (gross/advance/paid/outstanding, payment history, STAFF-only Record Payment / Apply Advance / Settle in Full). OWNER sees all information without mutation controls.

## 8.3 Income, Expenses & Dashboard

- **Income is derived, never entered**: income is **not** a manual ledger anymore. `GET /api/v1/income/`, `GET /api/v1/income/{id}/` and `GET /api/v1/income/summary/` read the customer payments recorded in the billing app (Phase 11); every non-refund payment (ADVANCE / PARTIAL / FINAL) contributes to income exactly once and refunds reduce net income (a refund is never positive). `POST /income/` no longer exists; payments and refunds are recorded through the invoice payment API.
- **Income summary**: `GET /api/v1/income/summary/` (OWNER + STAFF, read-only) returns `total_income`, `payment_count`, `refund_count`, `total_refunds`, `by_payment_method` and `by_payment_type`. Filters on both the list and the summary: `date_from`, `date_to`, `payment_method`, `payment_type` (all validated; invalid values → 400; inclusive date boundaries).
- **Expense records**: `GET/POST /api/v1/expenses/`, detail `GET /api/v1/expenses/{id}/`, summary `GET /api/v1/expenses/summary/`; filters `date_from`, `date_to`, `category`, `payment_method`, `page` (inclusive date boundaries). Categories: `RENT`, `ELECTRICITY`, `MATERIAL`, `MAINTENANCE`, `SHOP_SUPPLIES`, `TRANSPORT`, `OTHER_EXPENSE`. Create is STAFF-only and records `recorded_by` server-side; records are never updated or physically deleted. Both use `Decimal` money with `amount > 0` enforced at the database and serializer level.
- **Dashboard** `GET /api/v1/dashboard/summary/` (OWNER + STAFF, read-only) with optional `date_from` / `date_to`. Its `financial.recorded_income` is computed by the same shared aggregation service as the income API (so dashboard and income can never disagree), `recent_payments` shows the latest payment rows, and it also returns payroll paid from actual `PayrollPayment` records, salary advances as a separate metric, order revenue clearly distinguished from recorded cash income, and an `operational` block (order status counts, garment quantities, tailor workload, active customer/tailor counts). All arithmetic is derived on the fly from authoritative records.
- Frontend: `Dashboard` page (date-range filter, financial cards, order status, shop overview, tailor workload, recent income/expenses), a read-only `Income` page (summary cards, date/payment-method/payment-type filters, payment detail table with refund-aware amounts, breakdowns by method and type, pagination) and an `Expenses` page (summary cards, date/category/payment-method filters, pagination, STAFF-only Add dialog). OWNER sees all information without mutation controls. Navigation entries are added without touching existing modules.

## 8.4 Customer Billing & Invoice Foundation

- **Invoices**: `GET/POST /api/v1/invoices/`, detail `GET /api/v1/invoices/{id}/`, plus `POST /api/v1/orders/{id}/invoice/` as a convenience (creates the invoice and returns it). One invoice per order (enforced); each order gets a unique server-generated `invoice_number` of the form `INV-YYYY-NNNN`. Line items are immutable snapshots of the order garments (`garment_type`, `garment_code`, `quantity`, `unit_price`, `line_total`). `subtotal` and `total_amount` are stored; `adjustment_amount` is stored but always `0.00`; `created_by` is always the authenticated user.
- **Derived, never stored**: `amount_paid` (sum of payments), `balance_due` (total − paid), and `status` (`UNPAID` / `PARTIALLY_PAID` / `PAID`) are recomputed on every read. Invoices are never updated or deleted (no update/delete routes).
- **Customer payments**: `GET/POST /api/v1/invoices/{id}/payments/` — append-only history and STAFF-only recording (amount > 0, date, method `CASH` / `UPI` / `BANK_TRANSFER` / `OTHER`, reference, notes; `recorded_by` server-side). Payments are never edited or deleted.
- **Concurrency safety**: `record_customer_payment` runs in `transaction.atomic()` with `select_for_update()` on the invoice row, so concurrent payments can never push the invoice past its balance due.
- **Filters**: invoices by `search` (invoice/order number, customer name/mobile), `customer`, `order`, derived `status`, and inclusive `date_from` / `date_to`; payments by `payment_method` and inclusive dates.
- **RBAC**: anonymous → 401; OWNER is view-only (creating an invoice or recording a payment → 403); STAFF creates invoices and records payments.
- Frontend: new `Invoices` list (search / status / date filters, pagination, STAFF-only Create Invoice) and `InvoiceDetail` (summary, line items, payment history, STAFF-only Record Payment / Settle in Full), a navigation entry, and a non-invasive `View Invoice` / `Create Invoice` button on the order detail page.

## 8.5 Expense Management (Phase 12)

- **Expense records**: `GET/POST /api/v1/expenses/`, detail `GET /api/v1/expenses/{id}/`; filters `date_from`, `date_to`, `category`, `payment_method`, `page` (inclusive date boundaries). Categories: `RENT`, `ELECTRICITY`, `MATERIAL`, `MAINTENANCE`, `SHOP_SUPPLIES`, `TRANSPORT`, `OTHER_EXPENSE`. Payment methods match the project convention: `CASH` / `UPI` / `BANK_TRANSFER` / `OTHER`. Create is STAFF-only and records `recorded_by` server-side; records are never updated or physically deleted.
- **Expense summary**: `GET /api/v1/expenses/summary/` (OWNER + STAFF, read-only) returns `total_expenses`, `expense_count`, `by_category` and `by_payment_method`, honoring the same filters. Every figure is aggregated server-side from the expense records.
- **Validation**: `amount > 0` (DB `CheckConstraint` + serializer); category/payment method are controlled choices (anything else → 400); all money uses `Decimal`.
- Frontend: the `Expenses` page shows summary cards (total expenses, expense count, largest category), date/category/payment-method filters, a Payment Method column, and a STAFF-only Add Expense dialog with a Payment Method select. OWNER sees all information without mutation controls.

## 8.6 Reports & Business Insights (Phase 14)

- **Read-only reporting layer**: `GET /api/v1/reports/summary/` (OWNER + STAFF, read-only) aggregates order counts and status distribution, order revenue, garment quantities, customer activity, tailor workload, income, expenses, net position, payroll paid and salary advances — all derived on the fly from the authoritative modules (orders, customers, tailors, billing payments, expenses, payroll). Reports never create a second source of truth: income and expense figures reuse the same `build_income_summary` / `build_expense_summary` aggregations as the income and expense pages, and the net position is computed server-side (never stored).
- **Date filtering**: optional inclusive `date_from` / `date_to` apply consistently across every date-based metric (orders by `order_date`, customers by creation date, income/refunds by `payment_date`, expenses by `expense_date`, payroll by `payment_date`, advances by `advance_date`); invalid or reversed ranges → 400 with the standard error contract. Workload and active counts are live shop snapshots, matching the dashboard.
- **RBAC**: anonymous → 401; both OWNER and STAFF can read; there are no mutation endpoints (no POST/PUT/PATCH/DELETE).
- Frontend: a `Reports` page with From/To/Apply/Reset date filters, financial stat cards (net position, income, expenses, order revenue), operational cards (orders with status chips and garment quantities, customers, tailor workload, payroll & settlements) and breakdown tables (income by payment type, expenses by category). Loading, error and empty states follow the existing page patterns; React Query keys are invalidated whenever payments, refunds, expenses, orders, work assignments, payroll payments or salary advances change.
- **Exports (Phase 17)**: `GET /api/v1/reports/export/csv/` and `GET /api/v1/reports/export/pdf/` (OWNER + STAFF, read-only) produce a deterministic UTF-8 CSV and a printable PDF snapshot from the same authoritative `build_reports_summary` aggregation the page renders, honoring the same inclusive `date_from`/`date_to` semantics (no range = all time). File names are range-derived and safe (`saamu-tailors-report-<range>.csv|pdf`). The Reports page has Export CSV / Export PDF buttons that download the file for the applied range only, with loading/disabled states, duplicate-submit protection, recoverable error display and no navigation. PDF rendering uses `reportlab` (added to `backend/requirements.txt`).

## 8.7 Customer Communication & WhatsApp-Ready Delivery (Phase 18)

- **Preparation only, never sending**: `GET /api/v1/communications/messages/prepare/order/<order_id>/?message_type=...` (OWNER + STAFF, GET-only, read-only) returns `{success, data: {message_type, message, phone_number, whatsapp_url}}`. The server authors the plain-text message from authoritative order/customer/payment data (`order_payment_summary`); nothing is sent, stored or logged. The user then decides to copy the message or open WhatsApp in the browser (`https://wa.me/<number>?text=<encoded>`), so delivery is never claimed.
- **Four templates** with stable identifiers: `ORDER_ACKNOWLEDGEMENT` (name, order number/date, concise item summary, total, paid/balance when available, expected delivery), `ORDER_STATUS_UPDATE` (name, order number, current status, deterministic next step when the lifecycle defines a single one), `READY_FOR_COLLECTION` (only preparable when the order is actually `READY`, plus the database-backed shop location/phone), and `PAYMENT_BALANCE` (order number, total, paid, balance, authoritative payment state). Wording is centralized in `apps/billing/communications.py` and deterministic.
- **Safe phone handling**: only the existing `Customer.mobile_number` is used (no duplicate field, no migration). Harmless formatting is stripped; an explicit `+` country code is kept; a bare 10-digit Indian mobile (leading 6–9) is the only case where the `91` prefix is added (unambiguous for this India-only business); anything else is unusable and yields `phone_number: null` with no `whatsapp_url`. Numbers are never logged.
- **Errors**: unsupported message type / non-ready collection → 400 `validation_error`; missing order → 404 `not_found`; anonymous → 401; POST/PUT/PATCH/DELETE → 405. Standard `{success:false,error:{code,message,details?}}` contract preserved.
- **Frontend**: a reusable `OrderCommunicationPanel` on the Order Detail page (message-type select, compact preview, Copy WhatsApp Message with a 2-second copied state, Open WhatsApp disabled when no usable number with an explanation, loading/error/retry and duplicate-action protection). The frontend never calculates totals or balances.
- No WhatsApp Business/Meta Cloud/Twilio integration, no provider credentials, no webhooks, no background senders, no message history — all explicitly deferred.

---

## 9. Verification Commands

### Backend

```powershell
cd backend
.\.venv\Scripts\activate
python manage.py check
python -m pytest
black --check .
isort --check-only .
```

### Frontend

```powershell
cd frontend
npm run build
npx tsc --noEmit
npm run lint
npm run format   # prettier --write
```

---

## 9.1 Backup & Restore (Phase 16)

Backup/restore is an **operator workflow** (management commands), not a browser
feature. PostgreSQL-native tooling (`pg_dump` / `pg_restore` / `psql`) is used
with custom-format dumps stored outside the source tree.

```powershell
cd backend
.\.venv\Scripts\activate

python manage.py db_backup              # timestamped backup + verification
python manage.py db_list_backups        # list backups (newest first)
python manage.py db_verify --restore-test   # verify + disposable restore test
python manage.py db_restore --backup saamu_db_<timestamp>.dump   # destructive, requires confirmation
python manage.py db_cleanup --keep 10   # retention (dry-run by default; --execute to delete)
```

Key safety rules:

- `BACKUP_DIR` defaults to `%USERPROFILE%\SaamuBackups` (outside the repo) and
  is configurable in `backend/.env`.
- `PGBIN` points at the PostgreSQL tool directory when the tools are not on
  `PATH` (e.g. `C:\Program Files\PostgreSQL\18\bin`).
- Restore requires explicit confirmation and creates a fresh pre-restore safety
  backup first.
- A PostgreSQL dump contains only database data — media/uploads, static/build
  output, `.env` secrets, logs and source code are backed up separately.

Full procedures: `docs/phase-16/12_PHASE_16_BACKUP_RESTORE_RUNBOOK.md` and
`docs/phase-16/13_PHASE_16_LOCAL_TO_CLOUD_MIGRATION.md`.

---

## 10. Environment Configuration

Backend (`backend/.env.example`):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key (change in production) |
| `DEBUG` | Set to `False` in production |
| `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT` | PostgreSQL connection |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `TIME_ZONE` | e.g. `Asia/Kolkata` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |
| `LOG_LEVEL` / `LOG_DIR` | Logging level and directory (defaults: `INFO`, `backend/logs`) |
| `STATIC_ROOT` / `MEDIA_ROOT` | Optional overrides (project-relative by default, cloud-overridable) |
| `BACKUP_DIR` | Backup storage location, outside the source tree (default `%USERPROFILE%\SaamuBackups`) |
| `PGBIN` | Optional directory containing `pg_dump` / `pg_restore` / `psql` (e.g. `C:\Program Files\PostgreSQL\18\bin`) |

Frontend (`frontend/.env.example`):

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend API base URL (default `http://localhost:8000/api/v1`) |
| `VITE_APP_TITLE` | Application display title |

Never commit the real `.env` files. `.env.example` templates are committed; `.env` files are ignored.

---

## 11. Repository Layout

```text
saamu/
├── backend/
│   ├── .venv/
│   ├── apps/
│   │   ├── authentication/   # custom User model, roles, JWT auth, RBAC permissions
│   │   ├── common/           # health check, error handling, shared utilities
│   │   ├── customers/        # customers + tailoring measurements (Phase 3)
│   │   ├── orders/           # orders, order items, status workflow (Phase 4)
│   │   ├── tailors/          # tailors, piece rates, work assignments (Phase 5)
│   │   ├── attendance/       # daily tailor attendance records (Phase 6)
│   │   ├── payroll/          # payroll periods, per-tailor entries + salary configurations (Phase 6/10)
│   │   ├── payments/         # salary advances + payroll payments/settlement (Phase 7)
│   │   ├── finance/          # expenses + derived customer-payment income + dashboard summary (Phase 8/12/13)
│   │   └── billing/          # customer invoices, typed payments, digital bills + WhatsApp-ready communication (Phase 9/11/18)
│   ├── config/               # Django project settings
│   ├── logs/  media/  static/
│   ├── manage.py
│   ├── requirements.txt      # runtime dependencies
│   ├── requirements-dev.txt  # development dependencies (tests, tooling)
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
├── docs/
│   └── phase-0/              # product & architecture documentation
├── prompts/
├── .gitignore
└── README.md
```

---

## 12. API Conventions

- All application APIs are versioned under `/api/v1/`.
- API errors use a consistent shape:

```json
{
  "success": false,
  "error": {
    "code": "stable_error_code",
    "message": "Human-readable message"
  }
}
```

- List endpoints use pagination (20 items per page by default).
- Authentication is enforced via JWT (SimpleJWT). Public endpoints opt out explicitly (health check, login, refresh).
- Role-based authorization is enforced at the backend using the authenticated user's application role.

---

## 13. Phase Status

- **Phase 0 — Product & Architecture Validation:** complete
- **Phase 1 — Project Foundation:** complete
- **Phase 2 — Authentication & Role-Based Access:** complete
- **Phase 3 — Customers & Tailoring Measurements:** complete
- **Phase 4 — Orders & Tailoring Workflow:** complete
- **Phase 5 — Tailors, Workload & Piece-Rate Salary:** complete
- **Phase 6 — Attendance & Payroll Foundation:** complete
- **Phase 7 — Salary Payments, Advances & Payroll Settlement:** complete
- **Phase 8 — Income, Expenses & Financial Dashboard:** complete
- **Phase 9 — Customer Billing & Invoice Foundation:** complete
- **Phase 10 — Tailor Salary & Payroll:** complete
- **Phase 11 — Payments & Billing:** complete
- **Phase 12 — Expense Management:** complete
- **Phase 13 — Income Management (customer-payment-derived income):** complete
- **Phase 14 — Reports & Business Insights:** complete
- **Phase 15 — Production Hardening & Operational Readiness:** complete
- **Phase 16 — Backup, Restore & Data Portability:** complete
- **Phase 17 — Reports Export (CSV/PDF):** complete
- **Phase 18 — Customer Communication & WhatsApp-Ready Delivery:** complete
- **Phase 19+ — Business modules (automated reminders/sending, cloud migration):** pending

Do not treat this document as a feature guide; business functionality is implemented incrementally in later phases and documented in `docs/`.
