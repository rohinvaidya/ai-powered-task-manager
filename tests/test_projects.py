import pytest


async def _register_and_login(client, email="proj@example.com", username="projuser"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "secret123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "secret123"},
    )
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_create_project(client):
    token = await _register_and_login(client)
    response = await client.post(
        "/api/v1/projects",
        json={"name": "My Project", "description": "A test project"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Project"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(client):
    token = await _register_and_login(client, "list@example.com", "listuser")
    for i in range(3):
        await client.post(
            "/api/v1/projects",
            json={"name": f"Project {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = await client.get(
        "/api/v1/projects", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_update_project(client):
    token = await _register_and_login(client, "upd@example.com", "upduser")
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Old Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = create.json()["id"]
    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_project(client):
    token = await _register_and_login(client, "del@example.com", "deluser")
    create = await client.post(
        "/api/v1/projects",
        json={"name": "To Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = create.json()["id"]
    response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    get = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get.status_code == 404
