# Saamu Tailors - Tailoring Management System (ERP Foundation)

A scalable, production-ready enterprise application foundation for **Saamu Tailors**, engineered with React 19, TypeScript, Material UI, Vite, Django REST Framework, and PostgreSQL.

---

## 1. Folder Structure

```
d:\Projects\saamu\
├── .gitignore
├── README.md
├── docs/
│   └── README.md
├── prompts/
│   └── README.md
├── frontend/
│   ├── .env.example
│   ├── .eslintrc.cjs
│   ├── .gitignore
│   ├── .prettierrc
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── assets/
│       ├── components/
│       │   ├── Header.tsx
│       │   ├── Sidebar.tsx
│       │   └── Footer.tsx
│       ├── constants/
│       │   └── navigation.ts
│       ├── contexts/
│       ├── hooks/
│       │   └── useHealth.ts
│       ├── layouts/
│       │   └── MainLayout.tsx
│       ├── pages/
│       │   ├── Login.tsx
│       │   └── Placeholders.tsx
│       ├── routes/
│       │   └── AppRoutes.tsx
│       ├── services/
│       │   ├── apiClient.ts
│       │   └── healthService.ts
│       ├── styles/
│       │   └── global.css
│       ├── theme/
│       │   └── theme.ts
│       ├── types/
│       │   ├── api.ts
│       │   └── navigation.ts
│       ├── utils/
│       │   └── formatters.ts
│       ├── App.tsx
│       └── main.tsx
└── backend/
    ├── .env.example
    ├── .gitignore
    ├── manage.py
    ├── pyproject.toml
    ├── requirements.txt
    ├── config/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── apps/
    │   ├── __init__.py
    │   ├── authentication/
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   └── models.py
    │   └── common/
    │       ├── __init__.py
    │       ├── apps.py
    │       ├── urls.py
    │       └── views.py
    ├── media/
    ├── static/
    └── logs/
```

---

## 2. Installed Packages

### Frontend (`frontend/package.json`)
- **React**: `^19.0.0`
- **React DOM**: `^19.0.0`
- **TypeScript**: `~5.7.3`
- **Vite**: `^6.0.11`
- **Material UI**: `@mui/material` (`^6.4.2`), `@mui/icons-material` (`^6.4.2`), `@emotion/react`, `@emotion/styled`
- **Routing**: `react-router-dom` (`^7.1.5`)
- **HTTP Client**: `axios` (`^1.7.9`)
- **Data Fetching**: `@tanstack/react-query` (`^5.66.0`)
- **Form Handling & Validation**: `react-hook-form` (`^7.54.2`), `zod` (`^3.24.1`), `@hookform/resolvers` (`^3.9.1`)
- **Date Handling**: `dayjs` (`^1.11.13`)
- **Linting & Formatting**: `eslint`, `prettier`

### Backend (`backend/requirements.txt`)
- **Python Framework**: `Django>=5.0,<6.0`
- **API Framework**: `djangorestframework>=3.15.0`
- **CORS**: `django-cors-headers>=4.3.0`
- **Environment Management**: `python-dotenv>=1.0.1`
- **PostgreSQL Adapter**: `psycopg2-binary>=2.9.9`
- **Code Quality**: `black>=24.0.0`, `isort>=5.13.0`

---

## 3. Environment Variable Templates

### Backend (`backend/.env.example`)
```ini
SECRET_KEY=django-insecure-saamu-tailors-dev-key-change-in-production-123456
DEBUG=True

DATABASE_NAME=saamu_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432

ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
TIME_ZONE=Asia/Kolkata
```

### Frontend (`frontend/.env.example`)
```ini
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=Saamu Tailors
```

---

## 4. PostgreSQL Setup Instructions

1. Install PostgreSQL on Windows (or use your local PostgreSQL server).
2. Open PostgreSQL CLI (`psql`) or pgAdmin and run:
   ```sql
   CREATE DATABASE saamu_db;
   CREATE USER postgres WITH PASSWORD 'postgres';
   GRANT ALL PRIVILEGES ON DATABASE saamu_db TO postgres;
   ```
3. Copy `backend/.env.example` to `backend/.env` and update credentials if your local database username/password differ.

---

## 5. Commands to Run Backend

From the project root:

```bash
# 1. Navigate to backend directory
cd backend

# 2. (Optional) Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows PowerShell / CMD

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Run Django database migrations
python manage.py makemigrations
python manage.py migrate

# 5. Start Django development server
python manage.py runserver 8000
```
- Health Check API will be live at: `http://localhost:8000/api/v1/health/`

---

## 6. Commands to Run Frontend

From the project root:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install node dependencies
npm install

# 3. Start Vite development server
npm run dev
```
- React application will open at: `http://localhost:5173/`

---

## 7. Manual Steps Required After Code Generation

1. **Verify Local PostgreSQL Service**: Ensure PostgreSQL service (`postgresql-x64-16` or similar) is started and accessible at `localhost:5432`.
2. **Execute Migrations**: Run `python manage.py makemigrations` and `python manage.py migrate` to apply the custom `authentication.User` model schema to your PostgreSQL database.
3. **Create Superuser (Optional)**:
   ```bash
   python manage.py createsuperuser
   ```
4. **Health Check Verification**: Open `http://localhost:8000/api/v1/health/` in your browser or curl to confirm response:
   ```json
   {
       "status": "ok",
       "application": "Saamu Tailors",
       "version": "1.0"
   }
   ```
5. **Launch Application**: Open `http://localhost:5173` in your browser to view the login screen and navigate through the ERP placeholder pages.
