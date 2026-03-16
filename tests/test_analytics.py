import pytest
from tests.conftest import create_project, create_task, register_and_login


@pytest.mark.asyncio
async def test_analytics_empty(client):
    """User with no projects gets zeroed-out analytics."""
    token = await register_and_login(client, "anon@example.com", "anonuser")
    response = await client.get("/api/v1/analytics/me",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 0
    assert data["completion_rate_pct"] == 0.0
    assert data["overdue_tasks"] == 0
    assert data["project_count"] == 0


@pytest.mark.asyncio
async def test_analytics_counts_tasks(client):
    token = await register_and_login(client, "count@example.com", "countuser")
    project_id = await create_project(client, token)
    await create_task(client, token, project_id, "Task 1")
    await create_task(client, token, project_id, "Task 2")
    await create_task(client, token, project_id, "Task 3")

    response = await client.get("/api/v1/analytics/me",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 3
    assert data["project_count"] == 1


@pytest.mark.asyncio
async def test_analytics_completion_rate(client):
    token = await register_and_login(client, "rate@example.com", "rateuser")
    project_id = await create_project(client, token)

    t1 = await create_task(client, token, project_id, "Done 1")
    t2 = await create_task(client, token, project_id, "Done 2")
    await create_task(client, token, project_id, "Todo")

    # Mark 2 out of 3 as done
    for task in [t1, t2]:
        await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task['id']}",
            json={"status": "done"},
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get("/api/v1/analytics/me",
        headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert data["completion_rate_pct"] == pytest.approx(66.7, abs=0.1)


@pytest.mark.asyncio
async def test_analytics_by_status(client):
    token = await register_and_login(client, "status@example.com", "statususer")
    project_id = await create_project(client, token)

    t = await create_task(client, token, project_id, "In progress task")
    await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{t['id']}",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await create_task(client, token, project_id, "Todo task")

    response = await client.get("/api/v1/analytics/me",
        headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert data["by_status"].get("in_progress", 0) == 1
    assert data["by_status"].get("todo", 0) == 1


@pytest.mark.asyncio
async def test_analytics_by_priority(client):
    token = await register_and_login(client, "pri@example.com", "priuser")
    project_id = await create_project(client, token)
    await create_task(client, token, project_id, "Urgent", priority="urgent")
    await create_task(client, token, project_id, "Low", priority="low")

    response = await client.get("/api/v1/analytics/me",
        headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert data["by_priority"].get("urgent", 0) == 1
    assert data["by_priority"].get("low", 0) == 1


@pytest.mark.asyncio
async def test_project_analytics(client):
    token = await register_and_login(client, "projanalytics@example.com", "projanalyticsuser")
    project_id = await create_project(client, token, "Analytics Project")
    await create_task(client, token, project_id, "Task A")
    await create_task(client, token, project_id, "Task B")

    response = await client.get(f"/api/v1/analytics/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_id
    assert data["total_tasks"] == 2
    assert data["completion_rate_pct"] == 0.0


@pytest.mark.asyncio
async def test_project_analytics_not_found(client):
    token = await register_and_login(client, "nfanalytics@example.com", "nfanalyticsuser")
    response = await client.get("/api/v1/analytics/projects/nonexistent",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analytics_unauthenticated(client):
    response = await client.get("/api/v1/analytics/me")
    assert response.status_code == 403
