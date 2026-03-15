# Tech Stack — Decisions & Rationale

This document explains every technology used in TaskFlow, why it was chosen, and how it fits into the overall architecture.

---

## Backend

### FastAPI (Python)

**What it is:** A modern async Python web framework for building APIs.

**Why we used it:**
FastAPI was chosen over Flask and Django REST Framework for three reasons. First, it is built on ASGI and supports `async/await` natively, which is essential for a backend that makes concurrent calls to the database, Redis cache, and external APIs (Claude) within a single request. Second, it auto-generates OpenAPI documentation from type hints, eliminating the need to maintain a separate API spec. Third, Pydantic is a first-class citizen, meaning request validation, serialization, and response shaping happen automatically with zero boilerplate.

**How it's used:**
Every route is an async function. The app is structured around versioned routers (`/api/v1/...`), registered in `app/main.py`. The lifespan context manager handles startup (DB table creation) and shutdown (engine disposal) cleanly.

---

### SQLAlchemy 2.0 (Async ORM)

**What it is:** Python's most widely used ORM, used here in its modern async mode.

**Why we used it:**
SQLAlchemy 2.0 introduced a fully async API via `create_async_engine` and `AsyncSession`. This means DB queries don't block the event loop, which is critical when many concurrent requests share the same server. The ORM layer also gives us type-safe models, relationship definitions, and migration support via Alembic — without writing raw SQL for every query.

**How it's used:**
Three models are defined in `app/models/` — `User`, `Project`, and `Task`. Each maps to a PostgreSQL table. All queries in routers and services use `await db.execute(select(...))` patterns with the async session injected as a FastAPI dependency.

---

### PostgreSQL

**What it is:** A production-grade relational database.

**Why we used it:**
Tasks, projects, and users have clear relational structure — projects belong to users, tasks belong to projects, tasks can be assigned to users. PostgreSQL handles these foreign key relationships, cascading deletes, and complex filtered queries (by status, priority, due date) efficiently and reliably. It also supports enum types, which map directly to our `TaskStatus` and `TaskPriority` enums.

**How it's used:**
The database schema is defined via SQLAlchemy models and applied through Alembic migrations. The connection is async via the `asyncpg` driver. For local development, a native PostgreSQL install is used to avoid WSL2/Docker networking issues.

---

### asyncpg

**What it is:** A fast, pure-Python async PostgreSQL driver.

**Why we used it:**
SQLAlchemy's async engine requires an async-compatible database driver. `asyncpg` is the most performant option for PostgreSQL — it speaks the PostgreSQL binary protocol directly and is significantly faster than `psycopg2` for async workloads.

**How it's used:**
Specified in the `DATABASE_URL` as `postgresql+asyncpg://...`. SQLAlchemy handles the driver lifecycle automatically.

---

### Alembic

**What it is:** A database migration tool built for SQLAlchemy.

**Why we used it:**
As the schema evolves (adding columns, changing types, new tables), we need a versioned, reproducible way to apply those changes to any environment. Alembic generates migration scripts that can be run forward or rolled back, making deployments and team collaboration safe.

**How it's used:**
Migration scripts live in `alembic/versions/`. The `alembic/env.py` imports our SQLAlchemy models and configures the async engine. New migrations are generated with `alembic revision --autogenerate -m "description"` and applied with `alembic upgrade head`.

---

### Redis

**What it is:** An in-memory key-value store used for caching and as a message broker.

**Why we used it:**
Redis serves two distinct roles in this project. As a **cache**, it stores serialized task list and project list query results with a 5-minute TTL, avoiding repeated database reads for frequently accessed data. As a **message broker**, it connects FastAPI to Celery, queuing background jobs for asynchronous processing.

**How it's used:**
The `app/core/redis.py` module provides `cache_set`, `cache_get`, and `cache_delete_pattern` helpers used in the project and task routers. Cache keys follow the pattern `tasks:{project_id}:list:{status}:{priority}`. On any mutation (create/update/delete), the relevant key pattern is invalidated.

---

### Celery

**What it is:** A distributed task queue for running background jobs asynchronously.

**Why we used it:**
Sending notifications and scanning for overdue tasks should not happen inside the HTTP request lifecycle — they would add latency and could fail silently. Celery moves these operations to background worker processes that run independently of the web server, with retry logic and scheduling built in.

**How it's used:**
Two worker modules are defined in `app/workers/`. `reminder_worker.py` runs on a schedule (every 5 minutes via Celery Beat) to scan for overdue tasks and queue notification jobs. `notification_worker.py` sends emails when credentials are configured, or logs to stdout in development. Workers are started separately: `celery -A app.core.celery_app worker`.

---

### Anthropic Claude API

**What it is:** A large language model API for AI-powered features.

**Why we used it:**
Task priority is inherently subjective and context-dependent — due dates, task descriptions, and workload patterns all matter. Rather than hardcoding priority rules, we delegate this reasoning to Claude, which can analyze a full task list and return structured priority suggestions with explanations. This makes the AI feature genuinely useful rather than a shallow heuristic.

**How it's used:**
`app/services/ai_service.py` calls `claude-sonnet-4-20250514` with a strict system prompt requiring JSON-only responses. The prompt includes all tasks with their title, status, priority, and due date. The response is parsed and returned via the `/ai/projects/{id}/suggest-priorities` endpoint. If `ANTHROPIC_API_KEY` is not set, a rule-based fallback (due date proximity) is used automatically.

---

### Pydantic v2 + pydantic-settings

**What it is:** A data validation library and settings management tool.

**Why we used it:**
Pydantic handles all request/response serialization in FastAPI. Every API input is validated against a schema before touching the database — wrong types, missing fields, and invalid formats are rejected automatically with clear error messages. `pydantic-settings` extends this to environment variable loading, giving us typed, validated configuration from `.env` files.

**How it's used:**
`app/schemas/` contains one schema file per model. `app/core/config.py` defines the `Settings` class that reads from `.env` at startup. Field validators ensure `DATABASE_URL` and `SECRET_KEY` are never empty.

---

### python-jose + passlib

**What it is:** JWT encoding/decoding and password hashing libraries.

**Why we used it:**
Security primitives should never be implemented from scratch. `python-jose` handles JWT creation and verification with proper algorithm support (HS256). `passlib` with the bcrypt backend handles password hashing with automatic salting and a work factor appropriate for production.

**How it's used:**
`app/core/security.py` exposes four functions: `hash_password`, `verify_password`, `create_access_token`, and `decode_access_token`. The auth router uses these directly. The `get_current_user` dependency in `app/core/dependencies.py` decodes the Bearer token on every protected request.

---

### slowapi

**What it is:** A rate limiting middleware for FastAPI/Starlette.

**Why we used it:**
Without rate limiting, the API is vulnerable to brute-force attacks on the login endpoint and resource exhaustion from excessive requests. slowapi integrates cleanly with FastAPI's middleware system.

**How it's used:**
Configured in `app/main.py` with a default limit of 200 requests per minute per IP. The `SlowAPIMiddleware` is added to the app and the `RateLimitExceeded` exception handler returns a proper 429 response.

---

### prometheus-fastapi-instrumentator

**What it is:** Automatic Prometheus metrics instrumentation for FastAPI.

**Why we used it:**
For a backend designed for cloud deployment, observability is non-negotiable. Prometheus metrics expose request counts, latency histograms, and error rates in a format that Grafana, Datadog, and most cloud monitoring platforms can scrape.

**How it's used:**
A single call in `app/main.py` — `Instrumentator().instrument(app).expose(app)` — exposes the `/metrics` endpoint with default HTTP metrics. No additional configuration is needed.

---

## Frontend

### React 18

**What it is:** A component-based JavaScript UI library.

**Why we used it:**
The dashboard requires reactive state — selecting a project updates the task list, completing a task updates analytics, AI suggestions reorder priorities. React's component model and state management are well-suited to this kind of data-driven UI. React 18's concurrent features also allow for smooth loading states without janky renders.

**How it's used:**
The app has four pages (Landing, Login, Register, Dashboard) and uses React context (`useAuth`) for global auth state. The Dashboard manages local state for projects, tasks, suggestions, and analytics with `useState` and `useEffect`, calling the backend API via Axios.

---

### React Router v6

**What it is:** Client-side routing for React applications.

**Why we used it:**
The app has distinct pages (landing, auth, dashboard) that should have their own URLs for bookmarking and direct navigation. React Router v6 provides declarative routing with nested route support and the `Navigate` component for protected route redirects.

**How it's used:**
`App.jsx` defines four routes. `/dashboard` is wrapped in a `ProtectedRoute` component that checks the auth context and redirects to `/login` if no user is present. `/login` and `/register` are wrapped in `PublicRoute` which redirects authenticated users to the dashboard.

---

### Axios

**What it is:** A Promise-based HTTP client for JavaScript.

**Why we used it:**
Axios provides a cleaner API than `fetch` for this use case — it supports request interceptors (for attaching JWT tokens to every request), response interceptors (for handling 401 redirects), and automatic JSON serialization. It also handles error responses more predictably than `fetch`.

**How it's used:**
`src/api/client.js` creates a single Axios instance with `baseURL: '/api/v1'`. A request interceptor reads the JWT from localStorage and attaches it as a Bearer token. A response interceptor catches 401 errors, clears the token, and redirects to `/login`.

---

### Vite 8

**What it is:** A modern frontend build tool and dev server.

**Why we used it:**
Vite's dev server uses native ES modules and serves files without bundling, making hot module replacement near-instant. For this project it also provides the proxy configuration that forwards `/api` requests to the FastAPI backend, eliminating CORS issues in development entirely.

**How it's used:**
`vite.config.js` configures the `@vitejs/plugin-react` plugin and a proxy rule. All `/api` requests from the React app are proxied to `http://localhost:8000`, so the frontend and backend behave as a single origin in development.

---

## Infrastructure

### Docker + Docker Compose

**What it is:** Containerization platform and multi-container orchestration tool.

**Why we used it:**
Docker ensures the app runs identically across development, CI, and production environments. Docker Compose defines the full local stack — app, PostgreSQL, and Redis — in a single file, allowing the entire backend to start with one command.

**How it's used:**
`docker-compose.yml` defines three services with health checks and dependency ordering. The app container mounts the project directory as a volume and runs with `--reload` for development. The Dockerfile uses Python 3.12-slim as the base image.

---

### Alembic (also listed under Backend)

Covered above. Alembic bridges the gap between SQLAlchemy model definitions and the actual database schema, providing version-controlled, reversible migrations.

---

## Testing

### pytest + pytest-asyncio

**What it is:** Python's most popular testing framework with async support.

**Why we used it:**
All route handlers are `async` functions, so tests need to await them. `pytest-asyncio` enables async test functions and fixtures. The test suite uses an in-memory SQLite database via `aiosqlite`, meaning tests run without any external services.

**How it's used:**
`tests/conftest.py` sets up the in-memory database, overrides the `get_db` dependency with a test session, and creates an `AsyncClient` (from `httpx`) that calls the FastAPI app directly without starting a real HTTP server. Three test files cover auth, projects, and tasks with positive and negative test cases.
