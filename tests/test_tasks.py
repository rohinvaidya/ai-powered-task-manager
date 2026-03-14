import pytest


async def _setup(client, email, username):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "secret123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "secret123"}
    )
    token = login.json()["access_token"]
    project = await client.post(
        "/api/v1/projects",
        json={"name": "Task Project"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return token, project.json()["id"]


@pytest.mark.asyncio
async def test_create_task(client):
    token, project_id = await _setup(client, "task@example.com", "taskuser")
    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "My Task", "priority": "high"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Task"
    assert data["priority"] == "high"
    assert data["status"] == "todo"


@pytest.mark.asyncio
async def test_list_tasks(client):
    token, project_id = await _setup(client, "tasklist@example.com", "tasklistuser")
    for i in range(4):
        await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": f"Task {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = await client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 4


@pytest.mark.asyncio
async def test_filter_tasks_by_status(client):
    token, project_id = await _setup(client, "filter@example.com", "filteruser")
    t = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Done task", "status": "done"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Todo task"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.get(
        f"/api/v1/projects/{project_id}/tasks?status=done",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["status"] == "done"


@pytest.mark.asyncio
async def test_update_task(client):
    token, project_id = await _setup(client, "updt@example.com", "updtuser")
    create = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Old"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create.json()["id"]
    response = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        json={"title": "Updated", "status": "in_progress"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_task(client):
    token, project_id = await _setup(client, "delt@example.com", "deltuser")
    create = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "To Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create.json()["id"]
    response = await client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204
