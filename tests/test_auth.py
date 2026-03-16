import pytest
from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "secret123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dupe@example.com", "username": "user1", "password": "secret123"}
    await client.post("/api/v1/auth/register", json=payload)
    payload["username"] = "user2"
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    await client.post("/api/v1/auth/register",
        json={"email": "a@example.com", "username": "shared", "password": "secret123"})
    response = await client.post("/api/v1/auth/register",
        json={"email": "b@example.com", "username": "shared", "password": "secret123"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register",
        json={"email": "login@example.com", "username": "loginuser", "password": "secret123"})
    response = await client.post("/api/v1/auth/login",
        json={"email": "login@example.com", "password": "secret123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register",
        json={"email": "wrong@example.com", "username": "wronguser", "password": "correct"})
    response = await client.post("/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "incorrect"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    response = await client.post("/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "secret"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client):
    token = await register_and_login(client, "me@example.com", "meuser")
    response = await client.get("/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    response = await client.get("/api/v1/users/me",
        headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
