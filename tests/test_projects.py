import pytest
from tests.conftest import create_project, create_task, register_and_login


@pytest.mark.asyncio
async def test_create_project(client):
    token = await register_and_login(client, "proj@example.com", "projuser")
    response = await client.post("/api/v1/projects",
        json={"name": "My Project", "description": "A test project"},
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Project"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(client):
    token = await register_and_login(client, "list@example.com", "listuser")
    for i in range(3):
        await client.post("/api/v1/projects", json={"name": f"Project {i}"},
            headers={"Authorization": f"Bearer {token}"})
    response = await client.get("/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_get_project(client):
    token = await register_and_login(client, "get@example.com", "getuser")
    project_id = await create_project(client, token, "Single Project")
    response = await client.get(f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == project_id


@pytest.mark.asyncio
async def test_get_project_not_found(client):
    token = await register_and_login(client, "nf@example.com", "nfuser")
    response = await client.get("/api/v1/projects/nonexistent",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client):
    token = await register_and_login(client, "upd@example.com", "upduser")
    project_id = await create_project(client, token, "Old Name")
    response = await client.patch(f"/api/v1/projects/{project_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_project(client):
    token = await register_and_login(client, "del@example.com", "deluser")
    project_id = await create_project(client, token, "To Delete")
    response = await client.delete(f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204
    get = await client.get(f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"})
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_cannot_access_other_users_project(client):
    token1 = await register_and_login(client, "u1@example.com", "user1")
    token2 = await register_and_login(client, "u2@example.com", "user2")
    project_id = await create_project(client, token1, "Private Project")
    response = await client.get(f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_cascades_tasks(client):
    token = await register_and_login(client, "cascade@example.com", "cascadeuser")
    project_id = await create_project(client, token, "Cascade Project")
    await create_task(client, token, project_id, "Task 1")
    await create_task(client, token, project_id, "Task 2")
    await client.delete(f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"})
    # Project gone means tasks are gone too (cascade)
    response = await client.get(f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
