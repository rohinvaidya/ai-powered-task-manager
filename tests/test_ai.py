"""
Integration tests for the AI suggestions endpoints.
Uses rule-based fallback (no ANTHROPIC_API_KEY needed).
"""
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
        json={"name": "AI Test Project"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return token, project.json()["id"]


@pytest.mark.asyncio
async def test_suggest_priorities_empty_project(client):
    token, project_id = await _setup(client, "ai1@test.com", "aiuser1")
    res = await client.get(
        f"/api/v1/ai/projects/{project_id}/suggest-priorities",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "message" in data or "suggestions" in data


@pytest.mark.asyncio
async def test_suggest_priorities_with_tasks(client):
    token, project_id = await _setup(client, "ai2@test.com", "aiuser2")

    # Create a few tasks
    for title in ["Write tests", "Fix bug", "Deploy app"]:
        await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": title, "priority": "medium"},
            headers={"Authorization": f"Bearer {token}"},
        )

    res = await client.get(
        f"/api/v1/ai/projects/{project_id}/suggest-priorities",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "suggestions" in data
    assert "groups" in data
    assert "summary" in data
    assert len(data["suggestions"]) == 3


@pytest.mark.asyncio
async def test_apply_suggestions(client):
    token, project_id = await _setup(client, "ai3@test.com", "aiuser3")

    await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Urgent task", "priority": "low"},
        headers={"Authorization": f"Bearer {token}"},
    )

    res = await client.post(
        f"/api/v1/ai/projects/{project_id}/apply-suggestions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "applied" in data
    assert "summary" in data
    assert "groups" in data


@pytest.mark.asyncio
async def test_suggest_priorities_wrong_project(client):
    token, _ = await _setup(client, "ai4@test.com", "aiuser4")
    res = await client.get(
        "/api/v1/ai/projects/nonexistent-id/suggest-priorities",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_suggest_priorities_unauthenticated(client):
    res = await client.get("/api/v1/ai/projects/some-id/suggest-priorities")
    assert res.status_code == 403
