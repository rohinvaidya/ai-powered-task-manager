# TaskFlow — AI-Powered Backend Task Manager

A production-grade task management system built with FastAPI, PostgreSQL, Redis, Celery, and Claude AI. Features a React dashboard for managing tasks, AI-driven priority suggestions, background workers, analytics, and cloud-native deployment.

---

## Features

- **REST API** — Full CRUD for users, projects, and tasks with JWT authentication
- **AI Priority Engine** — Claude analyzes your tasks and returns priority suggestions and groupings
- **Background Workers** — Celery + Redis handles overdue reminders and status-change notifications
- **Analytics** — Per-user and per-project task statistics (completion rate, overdue count, by status/priority)
- **Redis Cache** — Task list and project queries are cached to reduce DB load
- **Rate Limiting** — 200 requests/minute per IP via slowapi
- **Prometheus Metrics** — Exposed at `/metrics` for scraping
- **React Dashboard** — Landing page, auth flow, kanban board, AI panel, and analytics tab
- **Docker + Kubernetes** — Compose for local development, K8s manifests for cloud deployment

---

## Project Structure

```
ai-powered-task-manager/
├── app/
│   ├── core/
│   │   ├── celery_app.py       # Celery app + beat schedule
│   │   ├── config.py           # Pydantic settings from .env
│   │   ├── database.py         # Async SQLAlchemy engine + session
│   │   ├── dependencies.py     # JWT auth dependency injection
│   │   ├── redis.py            # Redis cache helpers
│   │   └── security.py         # bcrypt hashing + JWT encode/decode
│   ├── models/
│   │   ├── user.py             # User ORM model
│   │   ├── project.py          # Project ORM model
│   │   └── task.py             # Task ORM model (status/priority enums)
│   ├── schemas/
│   │   ├── user.py             # UserCreate, UserResponse, TokenResponse
│   │   ├── project.py          # ProjectCreate/Update/Response
│   │   └── task.py             # TaskCreate/Update/Response
│   ├── routers/
│   │   ├── auth.py             # POST /register, /login
│   │   ├── users.py            # GET /users/me
│   │   ├── projects.py         # Full CRUD + Redis cache invalidation
│   │   ├── tasks.py            # Full CRUD + status/priority filters
│   │   ├── ai.py               # AI suggestions + apply endpoints
│   │   └── analytics.py        # User and project analytics
│   ├── services/
│   │   ├── ai_service.py       # Claude API integration + rule-based fallback
│   │   └── analytics_service.py # Task statistics queries
│   ├── workers/
│   │   ├── reminder_worker.py  # Overdue task scanner (Celery beat)
│   │   └── notification_worker.py # Email/log notifications
│   └── main.py                 # FastAPI app, middleware, router registration
├── frontend/
│   ├── src/
│   │   ├── api/client.js       # Axios API client with JWT interceptors
│   │   ├── hooks/useAuth.jsx   # Auth context + token management
│   │   ├── pages/
│   │   │   ├── Landing.jsx     # Marketing landing page
│   │   │   ├── Login.jsx       # Sign-in form
│   │   │   ├── Register.jsx    # Registration form
│   │   │   └── Dashboard.jsx   # Main app (kanban, AI panel, analytics)
│   │   ├── App.jsx             # Router + protected routes
│   │   └── main.jsx            # React entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── alembic/                    # DB migration scripts
├── tests/                      # pytest test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env
```

---

## Quickstart

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL (local install or Docker)
- Redis (Docker recommended)

### 1. Clone and set up the backend

```bash
git clone https://github.com/yourname/ai-powered-task-manager
cd ai-powered-task-manager

python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate        # macOS/Linux

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure environment

Copy `.env` and fill in your values:

```bash
cp .env .env.local
```

Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async URL e.g. `postgresql+asyncpg://user:pass@localhost:5432/taskdb` |
| `REDIS_URL` | Redis URL e.g. `redis://localhost:6379/0` |
| `SECRET_KEY` | Long random string for JWT signing |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (optional — falls back to rule-based AI) |

### 3. Set up the database

```sql
-- Run in psql or pgAdmin
CREATE USER taskuser WITH PASSWORD 'taskpass';
CREATE DATABASE taskdb OWNER taskuser;
GRANT ALL PRIVILEGES ON DATABASE taskdb TO taskuser;
```

### 4. Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 5. Run the backend

```bash
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

### 6. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at `http://localhost:3000`

### 7. Run background workers (optional)

```bash
# Worker process
celery -A app.core.celery_app worker --loglevel=info

# Beat scheduler (runs overdue checks every 5 min)
celery -A app.core.celery_app beat --loglevel=info
```

### 8. Run tests

```bash
pytest
```

---

## API Reference

All endpoints are prefixed with `/api/v1`.

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT token |

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/me` | Get current authenticated user |

### Projects

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects` | List all projects |
| POST | `/projects` | Create a project |
| GET | `/projects/{id}` | Get a project |
| PATCH | `/projects/{id}` | Update a project |
| DELETE | `/projects/{id}` | Delete a project |

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/tasks` | List tasks (filterable by status/priority) |
| POST | `/projects/{id}/tasks` | Create a task |
| GET | `/projects/{id}/tasks/{tid}` | Get a task |
| PATCH | `/projects/{id}/tasks/{tid}` | Update a task |
| DELETE | `/projects/{id}/tasks/{tid}` | Delete a task |

### AI

| Method | Endpoint | Description |
|---|---|---|
| GET | `/ai/projects/{id}/suggest-priorities` | Get AI priority suggestions |
| POST | `/ai/projects/{id}/apply-suggestions` | Apply suggestions to tasks |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/me` | User-wide task statistics |
| GET | `/analytics/projects/{id}` | Per-project statistics |

---

## Docker

Run the full stack (app + postgres + redis) with:

```bash
docker-compose up --build
```

---

## Task Model

| Field | Type | Values |
|---|---|---|
| `status` | enum | `todo`, `in_progress`, `done`, `cancelled` |
| `priority` | enum | `low`, `medium`, `high`, `urgent` |
| `due_date` | datetime | ISO 8601, optional |
| `assignee_id` | string | User ID, optional |

---

## Environment Variables

| Variable | Default | Required |
|---|---|---|
| `DATABASE_URL` | — | ✅ |
| `SECRET_KEY` | — | ✅ |
| `REDIS_URL` | `redis://localhost:6379/0` | |
| `ANTHROPIC_API_KEY` | — | Optional |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | |
| `MAIL_USERNAME` | — | Optional |
| `MAIL_PASSWORD` | — | Optional |
| `MAIL_FROM` | `noreply@taskmanager.dev` | |
| `MAIL_SERVER` | `smtp.gmail.com` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | |
| `DEBUG` | `false` | |
