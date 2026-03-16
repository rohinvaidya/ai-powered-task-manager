import pytest
from tests.conftest import create_project, create_task, register_and_login


@pytest.mark.asyncio
async def test_create_task(client):
    token = await register_and_login(client, "task@example.com", "taskuser")
    project_id = await create_project(client, token)
    response = await client.post(f"/api/v1/projects/{project_id}/tasks",
        json={"title": "My Task", "priority": "high"},
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Task"
    assert data["priority"] == "high"
    assert data["status"] == "todo"


@pytest.mark.asyncio
async def test_list_tasks(client):
    token = await register_and_login(client, "tasklist@example.com", "tasklistuser")
    project_id = await create_project(client, token)
    for i in range(4):
        await create_task(client, token, project_id, f"Task {i}")
    response = await client.get(f"/api/v1/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 4


@pytest.mark.asyncio
async def test_filter_tasks_by_status(client):
    token = await register_and_login(client, "filter@example.com", "filteruser")
    project_id = await create_project(client, token)
    await create_task(client, token, project_id, "Done task", status="done")
    await create_task(client, token, project_id, "Todo task")
    response = await client.get(f"/api/v1/projects/{project_id}/tasks?status=done",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["status"] == "done"


@pytest.mark.asyncio
async def test_filter_tasks_by_priority(client):
    token = await register_and_login(client, "filterpri@example.com", "filterpriuser")
    project_id = await create_project(client, token)
    await create_task(client, token, project_id, "Urgent task", priority="urgent")
    await create_task(client, token, project_id, "Low task", priority="low")
    response = await client.get(f"/api/v1/projects/{project_id}/tasks?priority=urgent",
        headers={"Authorization": f"Bearer {token}"})
    tasks = response.json()
    assert all(t["priority"] == "urgent" for t in tasks)


@pytest.mark.asyncio
async def test_get_task(client):
    token = await register_and_login(client, "gettask@example.com", "gettaskuser")
    project_id = await create_project(client, token)
    task = await create_task(client, token, project_id, "Single Task")
    response = await client.get(f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == task["id"]


@pytest.mark.asyncio
async def test_update_task(client):
    token = await register_and_login(client, "updt@example.com", "updtuser")
    project_id = await create_project(client, token)
    task = await create_task(client, token, project_id, "Old")
    response = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        json={"title": "Updated", "status": "in_progress"},
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_task_priority(client):
    token = await register_and_login(client, "updpri@example.com", "updpriuser")
    project_id = await create_project(client, token)
    task = await create_task(client, token, project_id, "Task", priority="low")
    response = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        json={"priority": "urgent"},
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["priority"] == "urgent"


@pytest.mark.asyncio
async def test_delete_task(client):
    token = await register_and_login(client, "delt@example.com", "deltuser")
    project_id = await create_project(client, token)
    task = await create_task(client, token, project_id, "To Delete")
    response = await client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    token = await register_and_login(client, "nftask@example.com", "nftaskuser")
    project_id = await create_project(client, token)
    response = await client.get(f"/api/v1/projects/{project_id}/tasks/nonexistent",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_task_belongs_to_project(client):
    token = await register_and_login(client, "iso@example.com", "isouser")
    project1 = await create_project(client, token, "Project 1")
    project2 = await create_project(client, token, "Project 2")
    task = await create_task(client, token, project1, "Project 1 task")
    # Task from project 1 should not be visible under project 2
    response = await client.get(f"/api/v1/projects/{project2}/tasks/{task['id']}",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
