import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# SQLite in-memory — no Docker required
# Use check_same_thread=False for async SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# SQLite doesn't enforce foreign keys by default — enable them
@event.listens_for(test_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        # native_enum=False makes SQLAlchemy use VARCHAR instead of DB-level ENUMs
        # which SQLite doesn't support natively
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, checkfirst=True
            )
        )
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Shared helpers ────────────────────────────────────────────────────────────

async def register_and_login(client, email: str, username: str, password: str = "secret123") -> str:
    """Register a user and return their JWT token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return res.json()["access_token"]


async def create_project(client, token: str, name: str = "Test Project") -> str:
    """Create a project and return its ID."""
    res = await client.post(
        "/api/v1/projects",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    return res.json()["id"]


async def create_task(client, token: str, project_id: str, title: str, **kwargs) -> dict:
    """Create a task and return the full task dict."""
    res = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": title, **kwargs},
        headers={"Authorization": f"Bearer {token}"},
    )
    return res.json()
