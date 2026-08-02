# Saamu Tailors — Tailoring Management System

A custom tailoring management system for **Saamu Tailors**, a family tailoring business operating since 1954.

The application digitizes the shop's operations: customer records, orders, measurements, tailoring workflow, tailor workload, payments, income, expenses, digital bills, and delivery/collection tracking.

**Current stage:** Phase 1 (Project Foundation). Business modules are implemented in later phases.

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

## 6. Verification Commands

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

## 7. Environment Configuration

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

Frontend (`frontend/.env.example`):

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend API base URL (default `http://localhost:8000/api/v1`) |
| `VITE_APP_TITLE` | Application display title |

Never commit the real `.env` files. `.env.example` templates are committed; `.env` files are ignored.

---

## 8. Repository Layout

```text
saamu/
├── backend/
│   ├── .venv/
│   ├── apps/
│   │   ├── authentication/   # custom User model
│   │   └── common/           # health check, error handling, shared utilities
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

## 9. API Conventions

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
- Authentication will be enforced in Phase 2 (JWT, role-based access).

---

## 10. Phase Status

- **Phase 0 — Product & Architecture Validation:** complete
- **Phase 1 — Project Foundation:** complete
- **Phase 2+ — Authentication, business modules:** pending

Do not treat this document as a feature guide; business functionality is implemented incrementally in later phases and documented in `docs/`.
