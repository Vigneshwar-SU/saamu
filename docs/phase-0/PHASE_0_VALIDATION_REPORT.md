# Saamu Tailors — Phase 0 Validation Report

**Author:** OpenCode (Lead Software Architect / Tech Lead)
**Date:** 2026-08-02
**Status:** READY FOR IMPLEMENTATION (foundation); business decisions gate later phases — see Section 14.

---

## 1. Executive Summary

Phase 0 documentation for Saamu Tailors was read in full and validated against the actual repository state. The product vision, workflow, scope, roles, business rules, architecture, domain model direction, API principles, and non-functional requirements are **internally consistent and sufficient to begin Phase 1**.

The repository contains a partially provisioned foundation scaffold:

- **Backend (Django 5.2 + DRF + PostgreSQL):** project structure, custom `User` model, one applied migration, health endpoint, environment-driven settings. It does **not currently boot** because `rest_framework_simplejwt` is referenced in `settings.py` but not installed in the active virtual environment.
- **Frontend (React 19 + Vite + MUI + TypeScript):** layout, theme, navigation, placeholder pages, API client, health hook. `node_modules` is only partially installed, so lint/build cannot run yet.
- **Database:** PostgreSQL 18 service is running; `saamu_db` exists and is reachable with the credentials in `backend/.env`.
- **Tooling gaps:** no git repository initialized, no tests, no logging configuration, DRF default permission is `AllowAny`, no pagination configured.

No blocking decisions affect **Phase 1 (Foundation), Phase 2 (Auth/RBAC), or Phase 3 (Master Data)**. Several business decisions are deferred by the Phase 0 documents themselves ("finalized during implementation") and gate specific later phases — most notably the tailor salary model (Phase 6) and garment measurement fields (Phases 4–5). These are enumerated in Section 14 and must be resolved before their phases begin, but they do not block the foundation.

---

## 2. Repository Assessment

### 2.1 What exists

```
D:\Projects\saamu\
├── .gitignore              # Comprehensive root ignore file (but no .git repo exists yet)
├── README.md               # Describes the scaffold, install commands, env templates
├── docs/
│   └── docs/phase-0/       # THE AUTHORITATIVE PHASE 0 DOCUMENTS (00–09)
├── prompts/README.md       # Empty prompt/notes placeholder
├── backend/
│   ├── .env / .env.example # Env config present; .env is gitignored
│   ├── manage.py
│   ├── requirements.txt    # Django, DRF, simplejwt, cors, dotenv, psycopg2, black, isort
│   ├── pyproject.toml      # black/isort config
│   ├── config/             # settings.py, urls.py, wsgi.py, asgi.py
│   ├── apps/authentication/  # Custom User (AbstractUser + phone_number); migration 0001_initial applied
│   ├── apps/common/          # Health check endpoint /api/v1/health/
│   ├── venv/ + env/          # TWO virtual environments (hygiene issue)
│   ├── logs/ static/ media/  # Empty runtime dirs with .gitkeep
└── frontend/
    ├── .env / .env.example
    ├── package.json        # Matches the Phase 0 frontend stack exactly
    ├── vite.config.ts      # Port 5173, /api proxy to :8000
    ├── tsconfig, eslintrc, prettierrc
    └── src/                # App, routes, layout, sidebar/header/footer, Login, placeholders,
                            # apiClient (interceptor placeholders), healthService, theme, types, utils
```

### 2.2 Key findings

| Area | Finding | Impact |
|---|---|---|
| Backend boot | `rest_framework_simplejwt` is in `INSTALLED_APPS` + `requirements.txt` but **not installed** in `venv/` | `python manage.py check` fails; backend cannot boot. Fix = `pip install -r requirements.txt` |
| Venvs | Two venvs: `venv/` (has Django/DRF/psycopg2, missing simplejwt) and `env/` (empty) | Confusion; consolidate to one |
| Database | PostgreSQL 18 service **Running**; `saamu_db` exists; 10 public tables (Django built-ins + auth migration applied); connection OK with `.env` credentials | Foundation DB is usable |
| Frontend deps | `node_modules` contains only `@mui`, `vite`, `zod` | `npm install` never completed; lint/build currently fail |
| Git | No `.git` directory despite `.gitignore` files | Work is unprotected; init a repo before Phase 1 |
| Tests | No test runner, no tests anywhere | NFR requires tests for important business logic |
| Logging | No `LOGGING` configuration in `settings.py` | NFR requires structured logging |
| DRF defaults | `DEFAULT_PERMISSION_CLASSES = AllowAny` | Security risk; should be `IsAuthenticated` by default |
| API versioning | `api/v1/` prefix wired in `config/urls.py` | Matches architecture decision |

### 2.3 Conflicting architecture decisions

None found in the repository scaffold that contradict Phase 0 documents. The scaffold is consistent with the documented stack. The defects listed above (missing package, incomplete `node_modules`, `AllowAny` default) are **implementation defects**, not architecture contradictions.

---

## 3. Product Understanding

**The shop.** Saamu Tailors is a family-run custom-tailoring business (est. 1954). Customers bring their own cloth; the shop manages cutting, stitching, ironing, storage, communication, payments, and delivery. Version 1 digitizes the manual paper process on a single Windows PC in the shop.

**Customers.** Individuals with a contact record (name, phone, address, notes, customer ID). One customer may have many orders. Historical records must be preserved. Duplicate detection matters (search by name/phone/ID before creating).

**Orders.** A customer transaction for tailoring. Contains one or more garment items. Has an order number, dates, notes, pricing, payments, and a status/timeline.

**Garments.** Distinct types of clothing (Shirt, Pant, Blouse, Churidar, Kurta, …). Each garment type may require different measurements. A garment instance in an order is an **OrderItem** (type + quantity + price + measurements + workflow status + tailor + notes).

**Measurements.** Garment-specific body measurements. They are captured per order/item as an **immutable snapshot** so history stays accurate; the customer's latest measurements can be copied into a new order as a starting point without mutating past orders.

**Cutting.** The owner/father cuts cloth per measurements. Workflow: Pending → In Progress → Completed. Cutting is tracked so the shop can see what is waiting.

**Tailors.** Workers who stitch garments. Each has a profile and an active/payment model. Work is tracked per garment (assignment, dates, status) so workload = active assignments, and completed work stays in history.

**Stitching.** The tailor's main task. Tracked per order item with assignment and status, enabling "what is each tailor working on", "how many pending", and "which orders are delayed".

**Ironing.** Post-stitching step for finished garments; tracked where applicable in the workflow.

**Locker/storage.** Finished garments are stored until collection. Track locker/location identifier, date stored, customer/order, collection status, so the shop can answer "where is this customer's finished garment?".

**Collection.** Customer arrives; staff find the order, verify the garment, check payment status, collect any balance, mark collected/delivered with date/time, and release the locker.

**Payments.** Money received from customers: advance, partial, final, balance tracking, refunds where required. Customer payment records are the **single source for income** (no duplicate income entry).

**Income.** Derived from customer payments (cash basis: payments received). Reported alongside expenses to compute net.

**Expenses.** Money spent: category, amount, date, description, payment method, recorded by. Financial records are not hard-deleted; controlled reversal/void preferred.

**Tailor salary.** Compensation paid to tailors. The model is **not yet defined** by the family (see Section 14) — a genuine open decision.

**Digital bills.** A printable/PDF bill per order/payment containing shop info, customer, order number, garment details, amounts, payments, balance, dates, and a bill identifier.

**Dashboard.** Operational overview calculated from real data: today's orders, in-progress, ready, pending collections, payments, expenses, tailor workload, pending balances, income, net.

---

## 4. Workflow Validation

The documented real-world workflow (02) maps cleanly to the software lifecycle:

```
Shop opening → Customer arrives (search/create) → New order (items, measurements, price, advance)
→ Cutting → Tailor assignment → Stitching → Ironing → Ready for collection → Locker
→ Contact customer → Collection (verify, settle balance, release locker) → Daily monitoring
```

**Validation:** The workflow is supported by the domain model (Order → OrderItem → Measurement snapshot → TailorAssignment → workflow status → Locker/collection → CustomerPayment). Status names are explicitly deferred to implementation.

**Clarifications needed before implementation:**

1. **Status granularity.** The business-rules state machine (05) lists order-level stages, but an order can contain multiple garments that progress independently (different tailors, different completion times). The operational status must be tracked **per OrderItem**, with the order-level status derived from its items. Needs to be finalized in Phase 5.
2. **Cutting placement.** Cutting is a per-garment (item-level) activity, matching the item-level workflow.
3. **Refund flow.** The workflow mentions refunds "where required"; no refund model is defined (see Section 14).
4. **"Contact customer" step.** Data for communication is captured in V1; automated WhatsApp/SMS is explicitly deferred to later in V1 (Phase 12).

---

## 5. Version 1 Scope Validation

### MUST HAVE — Version 1
- Auth & role-based access (Owner/Staff, JWT, owner-only staff admin)
- Shop & master data (shop profile, garment types, service types, configurable statuses)
- Customers (CRUD, search, history, contact details)
- Measurements (garment-specific, per-order snapshot, reuse, history)
- Orders (multi-item, pricing, notes, due date, advance, status, timeline)
- Cutting workflow
- Tailors (profiles, assignment, workload, current/completed work)
- Tailor salary/payment records (schema/model pending family decision)
- Customer payments (advance, partial, final, balance, history)
- Income (derived from payments)
- Expenses (records, categories, recorded-by)
- Delivery & locker (ready-for-collection, locker tracking, collection)
- Digital billing (PDF-ready bill)
- Notifications (prepared for WhatsApp/SMS; automation later)
- Dashboard (computed from real data)
- Reports (income, expenses, orders, garments, tailors, customers, payments, summaries)
- Settings (owner-level)
- Audit (important changes / financial actions)
- Backup (practical local strategy)

### OUT OF SCOPE — Version 1 (explicitly listed in 03)
Multi-branch, public customer portal, customer mobile app, online ordering, online payments, inventory/cloth stock, e-commerce, AI features, complex accounting/ERP, payroll tax compliance, cloud deployment, subscription billing, SaaS multi-tenancy.

### FUTURE
The out-of-scope list above becomes the Version 2+ backlog.

**Validation:** The scope matches the task instructions exactly. No scope expansion is proposed. One observation: **Notifications (WhatsApp/SMS)** sit on the boundary — 03 includes them as an "included module" but defers automation "after the core workflow is stable"; this is treated as the tail of V1 (Phase 12), which is consistent.

---

## 6. Role & Permission Validation

Exactly two roles: **OWNER** and **STAFF**. No additional business roles in V1.

- **OWNER** — full access, NOT view-only. Performs staff operations (the owner cuts cloth, takes orders, records payments) **and** administrative operations (staff account management, settings, audit, reports, salaries). Explicitly confirmed in 01, 04, and the task brief.
- **STAFF** — daily operational user. Creates/edits customers and orders, records measurements, updates workflow statuses, assigns/updates tailor work, views workload, records payments and expenses, generates bills, manages delivery/collection. Cannot manage staff accounts, change owner, touch system-level security settings, or perform owner-only administration.

**Validation:** The two-role model is consistent across all documents. The permission matrix is to be enforced **at the backend API level** (04, 06, 08) — the frontend hiding of buttons is supplemental only. Confirmed correct.

**Implementation note for Phase 2:** The current `User` model has no role field. Recommend an explicit `role` field (`OWNER`/`STAFF`) rather than Django groups, per Section 14. Also required: a bootstrap mechanism to create the initial OWNER account.

---

## 7. Architecture Review

The documented architecture is sound and cloud-migration-friendly:

```
React + TypeScript (Vite, MUI, TanStack Query, RHF+Zod)
        │ REST /api/v1/
        ↓
Django REST Framework (JWT, RBAC)
        ↓
PostgreSQL (only DB; no SQLite fallback)
```

### Frontend
- Stack matches 06 exactly (React 19, TS, Vite 6, MUI 6, Router 7, Axios, TanStack Query, RHF, Zod, Day.js). Package.json confirms.
- Skeleton is component/module-oriented (layout, theme, services, hooks, constants, types). Good foundation.
- `apiClient.ts` has placeholder interceptors (auth token injection, global error handling) — to be completed in Phase 2.

### Backend
- Django project layout with `apps/` package. **Caveat:** `settings.py` mutates `sys.path` (`sys.path.insert(0, BASE_DIR/"apps")`) to import `apps.*`. It works but is fragile; consider standardizing on a package layout or a proper `PYTHONPATH` when restructuring in Phase 1.
- DRF + SimpleJWT + CORS + dotenv are configured. Settings are environment-driven.

### Changes recommended BEFORE implementation (Phase 1):
1. **Install backend requirements** (missing `rest_framework_simplejwt`) — backend currently will not boot.
2. **Complete `frontend npm install`** — currently only 3 packages present.
3. **Default DRF permission** must become `IsAuthenticated` (secure by default), with explicit `AllowAny` only on health, login, and token endpoints. Current default `AllowAny` is a latent security hole.
4. **Add DRF default pagination** (e.g., `PageNumberPagination` 20/page) per 08.
5. **Add structured logging** (LOGGING dict → `logs/`), per 09.
6. **Add a DRF exception handler** returning the consistent error shape (message + field errors + stable code) per 08; never leak stack traces.
7. **Adopt a test baseline** (recommend `pytest` + `pytest-django`) per 09.
8. **Initialize a git repository** and commit the scaffold baseline (no repo exists today).
9. **Consolidate the two venvs** (`venv/` + `env/`) into one documented venv.
10. Make `MEDIA_ROOT`/`STATIC_ROOT` environment-configurable (small change, enables cloud later).

---

## 8. Domain Model Review

The proposed model correctly supports the required lifecycle:

```
Customer 1──* Order 1──* OrderItem
                            ├── Measurement Snapshot (immutable per item)
                            ├── Tailor Assignment
                            ├── Item workflow status (Cutting→Stitching→Ironing→Ready→Collected)
                            └── Locker / Delivery state
              └── CustomerPayment (source of income)
Tailor 1──* TailorAssignment; Tailor 1──* TailorSalary/Payment
Expense (category, amount, date, recorded-by)
AuditLog (user, action, entity, id, timestamp, context)
Shop → configuration/settings
```

### Strengths
- OrderItem as the granular unit correctly supports multi-garment orders, per-garment tailors, and per-garment progress.
- Immutable measurement snapshots satisfy the historical-integrity rule.
- Customer payments as the income source avoids double-entry.
- Audit log covers the "important changes" requirement.
- The doc correctly warns against overloading `Order`, duplicating income, storing only "latest measurements", using dashboard counters as source data, and hard-deleting financial history.

### Weaknesses / design decisions to lock down during implementation
1. **Measurement representation.** Options: (a) per-garment fixed columns, (b) normalized `MeasurementValue` (garment_type, field, value) rows, (c) immutable JSONB snapshot per OrderItem. Recommend (c) JSONB snapshot keyed by field name — flexible for differing garment types, trivially immutable, cloud-friendly, and field-level search is not a real requirement. The field *definitions* should come from a configurable measurement template per GarmentType.
2. **Item-level vs order-level status.** Recommend item-level status field + derived order status (aggregate). Track transitions and reject invalid transitions in a service layer; record a status history for auditability.
3. **Money.** Use `DecimalField` exclusively (NFR 09). Compute balances/totals in backend service methods, not the frontend.
4. **Locker.** `LockerLocation` catalog + nullable FK on OrderItem (set when stored, cleared on collection) with stored/collected timestamps. Collection releases the locker.
5. **TailorAssignment.** Dedicated model (tailor, item, assigned/completed dates, status). Workload = open assignments. Historical assignments remain.
6. **Refund model** is undefined (see Section 14).
7. **Deletion behavior.** Financial/operational history must not be hard-deleted; model as status/reversal/archive + audit.

### Historical data & auditability
Preserved via immutable measurement snapshots, retained payments/salary/order records, per-item status history, and the AuditLog. Confirmed adequate.

---

## 9. API Architecture Review

Matches 08: versioned `/api/v1/`, resource CRUD + action endpoints for meaningful operations, server-side search/filter, pagination, backend-enforced authorization, consistent error responses, OpenAPI/Swagger as optional documentation.

### Confirmed good
- Action-style endpoints (`/status/`, `/assign-tailor/`, `/collect/`) instead of blind table exposure.
- Dashboard/report endpoints return computed data from real records.
- Auth namespace (`/api/v1/auth/…`).
- Versioning precedent for `/api/v2/`.

### Recommendations
- Add staff administration endpoints under `/api/v1/users/` (owner-only) in Phase 2.
- Add master-data endpoints (garment types, measurement templates, payment methods, expense categories, locker locations, shop settings) in Phase 3.
- Add `/api/v1/audit/` (owner-only) once audit logging exists.
- Add an `audit` field convention (recorded_by, created_at) on all financial models.
- Keep pagination + server-side search on list endpoints from the start to avoid later refactors.

---

## 10. Security Review

| Area | Status | Action |
|---|---|---|
| Password hashing | Django default (PBKDF2/SHA-256 via `AbstractUser`) | OK |
| JWT | SimpleJWT, 60-min access, 1-day refresh, HS256 | OK; consider rotating refresh + blacklist for logout invalidation (Phase 2 decision) |
| Registration | No public registration | OK; owner creates staff accounts |
| Default permissions | DRF `AllowAny` — **unsafe default** | Change to `IsAuthenticated`; whitelist public endpoints |
| CORS | Restricted to configured origins from env | OK |
| Secrets | `.env` gitignored; no hard-coded secrets in code (dev-only defaults present, clearly marked) | OK; rotate before production |
| Error exposure | No custom exception handler yet; DRF default may leak traceback details in DEBUG | Add handler returning sanitized errors (Phase 1) |
| Input validation | DRF serializers | OK (backend authoritative) |
| RBAC | Not implemented yet | Phase 2; enforce at backend |
| Bootstrap owner | Not defined | Decision needed (Section 14) |
| Local PC | Single shared shop PC — consider screen-lock and DB access hygiene | Operational note |

---

## 11. Local Deployment Review

V1 runs on one Windows PC in the shop.

- **PostgreSQL 18** is already installed and running as a service on this machine (`postgresql-x64-18`, status Running). `saamu_db` is created and migrated (10 tables). Foundation is DB-ready.
- **Backend:** `runserver` is fine for development; for a production-like single-PC deployment, recommend **waitress** (pure-Python WSGI on Windows, no compiled deps) behind the Django static-serving of the built frontend. Startup via `.bat` scripts and Task Scheduler.
- **Frontend:** `vite build` → serve the `dist/` bundle (recommend `whitenoise` for static file serving through Django), keeping a single port (e.g., 8000 or 80) instead of two dev servers.
- Auto-start on PC boot via Windows Task Scheduler (Phase 14).

This is a Phase 14 concern; no foundation blocker. Note that deployment should be env-driven so the same code runs locally now and in the cloud later.

---

## 12. Future Cloud Migration Review

The architecture is cloud-ready by construction:

- No business logic touches the local filesystem or localhost except environment-driven `MEDIA_ROOT`/`STATIC_ROOT` (recommend making these env-configurable in Phase 1).
- Env-driven configuration for DB host/creds, allowed hosts, CORS, timezone.
- PostgreSQL as the sole DB is directly portable to any managed PostgreSQL.
- No Windows-specific code in business logic.
- The `sys.path` hack in `settings.py` is the only fragile bit worth normalizing (Section 7).

No redesign of business logic is required for a future cloud move. File storage (shop logo, bill assets) is the only area to keep abstracted for a future object store.

---

## 13. Backup & Data Safety Review

Backup is called out as a first-class concern for a local single-PC deployment (03, 06, 09). **No backup tooling exists yet.**

Requirements to implement (Phase 13, design now):
- Scheduled `pg_dump`/`pg_dumpall` job (Windows Task Scheduler) producing a dated dump.
- Retention policy (e.g., keep 30 days) and a copy to an external/secondary location (a shop PC hard-drive failure should not destroy the business records).
- Tested restore procedure (`pg_restore`) — documented and rehearsed before real data entry.
- Never rely on the database files themselves as the backup mechanism.

Additionally, since the app runs on one PC, treat the PostgreSQL service and its data directory as critical infrastructure: monitor disk space, keep PostgreSQL updated, and lock down DB credentials.

---

## 14. Missing Decisions

> Only decisions that **genuinely block or materially affect implementation** are listed. Each is ranked BLOCKING (must resolve before the named phase) or DEFERRABLE (can be settled during the phase with low risk).

### 1. Tailor salary / payment model — **BLOCKING (Phase 6)**
- **Missing:** How the shop actually pays tailors (per piece, per garment type, monthly, fixed + piece, advances against salary). Docs explicitly defer this ("after business rules are finalized").
- **Why it matters:** Drives the `TailorSalary`/`TailorPayment` schema and workload-to-salary linkage.
- **Options:** (a) per-garment piece rate by garment type; (b) fixed monthly salary with advance/payment records; (c) flexible "payment record" (amount + period + notes) without a rate engine.
- **Recommended:** (c) a simple, flexible payment-record model for V1 (amount, period/notes, recorded-by) that supports any compensation style; add a rate engine later if the shop wants one.

### 2. Garment types and measurement fields — **BLOCKING (Phases 4–5)**
- **Missing:** The final garment list (Shirt, Pant, Blouse, Churidar, Kurta, …?) and the exact measurement fields each requires. Doc: "Do not hard-code the final list without confirmation."
- **Why it matters:** Determines the measurement template/capture UX and the snapshot schema.
- **Options:** (a) fixed hard-coded list + fixed fields; (b) configurable GarmentType + per-type measurement field templates.
- **Recommended:** (b) configurable garment types with per-type measurement templates, seeded with the shop's actual list. Needs the family to confirm the garment list.

### 3. Exact order/item status state machine — **BLOCKING (Phase 5)**
- **Missing:** Final status values and allowed transitions (docs give two granularity sketches).
- **Why it matters:** Core workflow field and transition-validation logic.
- **Options:** (a) order-level only; (b) item-level statuses with derived order status.
- **Recommended:** (b) item-level: New → Cutting Pending → Cutting In Progress → Cutting Completed → Stitching → Ironing → Ready for Collection → Collected; plus Cancelled; derive the order status from items. Configurable/seedable list.

### 4. Income accounting interpretation — **BLOCKING (Phase 11)**
- **Missing:** Definition of "income" and "net" for reporting (cash vs accrual; income recognized on payment receipt vs order completion). Doc: "exact accounting interpretation … should be documented before financial reporting is finalized."
- **Why it matters:** Dashboard and report correctness; misrepresentation of business performance.
- **Options:** (a) cash basis — income = customer payments received; net = income − expenses; (b) accrual — income = order totals.
- **Recommended:** (a) cash basis, consistent with 05 ("Customer payments → Income"). Document it before Phase 11.

### 5. Refund model — **BLOCKING (Phase 7)**
- **Missing:** How refunds are recorded. 02 mentions refunds "where required"; 05 allows them only via an explicit model.
- **Why it matters:** Prevents invalid balances; preserves financial history.
- **Options:** (a) negative payment rows; (b) dedicated Refund record linked to a payment/order; (c) controlled reversal/void.
- **Recommended:** (b)/(c) — a dedicated refund/reversal record with audit, referenced by the original payment; enforce no-over-refund in the service layer.

### 6. Order number format — **BLOCKING (Phase 5)**
- **Missing:** "Unique human-readable order number" format.
- **Options:** sequential per year (`SMT-2026-0001`), date-based, global sequence.
- **Recommended:** `SMT-YYYY-NNNN` with a per-year sequence.

### 7. Payment methods list — **DEFERRABLE (Phase 7)**
- **Missing:** The list of accepted payment methods.
- **Options:** fixed vs configurable.
- **Recommended:** configurable master list seeded with Cash, UPI, Card, Bank Transfer.

### 8. Expense categories — **DEFERRABLE (Phase 8)**
- **Missing:** Expense category list.
- **Options:** fixed vs configurable.
- **Recommended:** configurable master list seeded with common categories (thread/supplies, zipper/buttons, rent, utilities, labor, transport, maintenance).

### 9. Locker identification scheme — **DEFERRABLE (Phase 9)**
- **Missing:** How lockers/racks are identified.
- **Options:** free-text, numeric IDs, rack+slot codes.
- **Recommended:** configurable short codes (e.g., `L1`…`L20`) maintained by the owner in Settings.

### 10. Bill numbering and scope — **DEFERRABLE (Phase 10)**
- **Missing:** Bill number format; whether the bill is per order or per payment.
- **Options:** per-order bill with sequence; per-payment receipt; both.
- **Recommended:** one bill per order (sequence `SMT-B-YYYY-NNNN`) plus a payment receipt on the same document; content per 02.

### 11. Initial OWNER bootstrap — **BLOCKING (Phase 2)**
- **Missing:** How the first OWNER account is created (no public registration).
- **Why it matters:** Without an owner, staff accounts cannot be created.
- **Options:** `createsuperuser` + manual role set; management command seeded from env; data migration.
- **Recommended:** a small management command (`create_owner`) reading `OWNER_USERNAME`/`OWNER_PASSWORD` from env (documented in `.env.example`), usable in Phase 2.

### 12. Local deployment method — **DEFERRABLE (Phase 14)**
- **Missing:** Production-like process stack and auto-start on the shop PC.
- **Options:** `runserver`; waitress + whitenoise; nginx on Windows.
- **Recommended:** waitress + whitenoise-served built frontend, `.bat` start scripts, Windows Task Scheduler autostart, PostgreSQL as a service.

### 13. Backup frequency / retention / location — **DEFERRABLE (Phase 13)**
- **Missing:** Schedule, retention, off-machine copy.
- **Options:** daily/weekly; retention windows; local vs external.
- **Recommended:** daily `pg_dump`, 30-day retention, weekly copy to an external drive, documented + tested restore.

### 14. WhatsApp/SMS provider — **DEFERRABLE (Phase 12)**
- **Missing:** Provider and channel details.
- **Why it matters:** Only when notifications are built; design for a provider abstraction so this is swappable.
- **Recommended:** keep the Notification model/channel abstraction now; choose provider at Phase 12 (Twilio / WhatsApp Business API / manual).

---

## 15. Contradictions

### Between Phase 0 documents
**No hard contradictions found.** All documents are consistent on roles (exactly two; owner is full-access, not view-only), PostgreSQL-only, JWT, no public registration, income derived from payments, backend-authoritative authorization, V1 scope boundaries, and historical-data preservation.

### Soft tensions / clarifications (not contradictions, but must be settled)
1. **Status granularity** — 05 lists order-level stages; the multi-item domain (07) implies item-level tracking. Both say "finalized during implementation." Settled in Section 14.3.
2. **Refunds** — 02 implies refunds may exist; 05 forbids negative payments unless an explicit refund model exists. No model is defined. Section 14.5.
3. **Income/net interpretation** — 05 gives the formula but defers the accounting interpretation. Section 14.4.
4. **Notifications timing** — 03 lists notifications as an included module but defers automation; treated as the tail of V1 (Phase 12). Consistent, noted.
5. **"Reset staff credentials where supported"** (04) — the "where supported" qualifier is ambiguous; resolve in Phase 2 (recommend: owner may reset a staff password).

### Documentation path structure
The authoritative docs originally lived at `docs/docs/phase-0/` (double-nested `docs/`) while 00 and the README referenced `docs/phase-0/`. This repository hygiene issue was corrected during Phase 1 by flattening to `docs/phase-0/`. This report is placed alongside the authoritative files.

### Code vs specification defects (implementation, not documentation)
- `rest_framework_simplejwt` missing from the active venv → backend does not boot.
- Frontend `node_modules` incomplete → build/lint fail.
- DRF default permission `AllowAny` → should be `IsAuthenticated`.
- No `LOGGING` configuration despite NFR 09.
- No git repository despite `.gitignore`.

---

## 16. Recommended Development Phases

The proposed phase list is technically sound and retained with minor clarifications. **Audit logging is pulled forward**: a lightweight `AuditLog` model and `recorded_by`/`created_at` conventions are introduced in Phase 1–2 because financial actions from Phase 5 onward depend on them.

```
Phase 0  — Product & Architecture Validation           [this report]
Phase 1  — Project Foundation
Phase 2  — Authentication & Role-Based Access
Phase 3  — Shop / Master Data
Phase 4  — Customers & Measurements
Phase 5  — Orders & Garment Workflow
Phase 6  — Tailors & Workload
Phase 7  — Payments & Income
Phase 8  — Expenses
Phase 9  — Delivery / Locker / Collection
Phase 10 — Digital Bills
Phase 11 — Dashboard & Reports
Phase 12 — Notifications (WhatsApp/SMS)
Phase 13 — Audit, Backup & Hardening
Phase 14 — Production Readiness & Local Deployment
```

### Phase 1 — Project Foundation
Fix the environment (install backend reqs incl. simplejwt, complete `npm install`), initialize git, consolidate venvs, secure DRF defaults (`IsAuthenticated`), add pagination, structured logging, a DRF exception handler for consistent errors, the `AuditLog` model + conventions, and the baseline test setup (`pytest` + `pytest-django`).

### Phase 2 — Authentication & RBAC
`role` field on `User` (OWNER/STAFF), JWT login/refresh/me/logout endpoints, `create_owner` bootstrap command, staff administration endpoints (owner-only), DRF permissions enforcing the matrix from 04, frontend auth context + route guards + apiClient interceptors.

### Phase 3 — Shop / Master Data
Shop profile/settings, GarmentType + measurement templates, configurable lists (payment methods, expense categories, locker locations, statuses/transitions) — all owner-editable, with the seeds from Section 14.

### Phase 4 — Customers & Measurements
Customer CRUD/search/history, measurement snapshot capture/reuse per Phase 14.2 (measurement template config gating this phase).

### Phase 5 — Orders & Garment Workflow
Order + OrderItem, order numbering (14.6), item-level status machine with transition validation + history (14.3), cutting workflow, due dates, pricing, notes, timeline. (Blocked until 14.2/14.3/14.6 are answered.)

### Phase 6 — Tailors & Workload
Tailor profiles, assignments, workload queries. (Blocked until 14.1 — salary model.)

### Phase 7 — Payments & Income
CustomerPayment CRUD with balance/overpayment validation, refund/reversal model (14.5), payment methods (14.7), income derivation. (Blocked until 14.5/14.7.)

### Phase 8 — Expenses
Expense CRUD with categories (14.8), recorded-by, no-hard-delete rules.

### Phase 9 — Delivery / Locker / Collection
Ready-for-collection, locker tracking (14.9), collection flow with balance settlement.

### Phase 10 — Digital Bills
PDF-ready bill generation (14.10), print from the shop PC.

### Phase 11 — Dashboard & Reports
Computed KPIs (14.4 income/net definition), query-driven reports.

### Phase 12 — Notifications
Notification model + provider abstraction; provider selection (14.12).

### Phase 13 — Audit, Backup & Hardening
Audit review/UI, backup job + tested restore (14.13), security hardening pass.

### Phase 14 — Production Readiness & Local Deployment
Waitress + whitenoise, startup scripts, autostart, final smoke test (14.12 local deployment method).

### Dependency graph
- 2 ← 1; 3 ← 1,2; 4 ← 3; 5 ← 3,4; 6 ← 5; 7 ← 5; 8 ← 3; 9 ← 5,7; 10 ← 5,7; 11 ← 5,7,8; 12 ← 5,9; 13 ← all; 14 ← all.

---

## 17. Risks

| # | Risk | Mitigation |
|---|---|---|
| 1 | Backend currently does not boot (missing `rest_framework_simplejwt`) | Install requirements in Phase 1 step 1 |
| 2 | Frontend `node_modules` incomplete; build/lint fail | Complete `npm install` in Phase 1 |
| 3 | No git repository — scaffold work unprotected | `git init` + baseline commit in Phase 1 |
| 4 | DRF default `AllowAny` — latent security hole | Flip to `IsAuthenticated` in Phase 1 |
| 5 | Deferred business decisions (14.1–14.6) gate Phases 4–6 | Resolve with the family before those phases; sections list recommended defaults |
| 6 | Single-PC data loss (drive failure / uninstall) | Scheduled + external-copy backups (Phase 13) **before** real data entry |
| 7 | Two venvs causing environment confusion | Consolidate to one documented venv |
| 8 | Owner participates in daily operations — risk of building a "view-only admin" | Mitigated: role design is explicit (04); enforce in Phase 2 |
| 9 | Cloud migration later | Keep file/storage paths env-configurable (Phase 1), avoid Windows/localhost assumptions in logic |
| 10 | Family may not want heavy data entry | Workflow doc principle: support current style, minimize typing (02 §15); keep forms minimal |
| 11 | `sys.path` hack in settings.py | Normalize package/import layout during Phase 1 refactor |

---

## 18. Final Recommendation

1. **Approve** the Phase 0 documentation baseline and proceed.
2. Begin **Phase 1 — Project Foundation**: fix the environment defects (backend deps incl. simplejwt, frontend install), initialize git, secure DRF defaults, add logging/error-handling/pagination, and establish the test baseline.
3. **Obtain the family's answers to the BLOCKING decisions in Section 14 before the corresponding phases begin** — in priority order: tailor salary model (before Phase 6), garment list + measurement fields (before Phase 4), order status machine + order-number format (before Phase 5), refund model + payment methods (before Phase 7), income/net interpretation (before Phase 11), initial owner bootstrap (before Phase 2).
4. Implement strictly per the documented phases; do not add out-of-scope features; keep the real tailoring workflow as the source of truth.

---

PHASE 0 STATUS: READY FOR IMPLEMENTATION
