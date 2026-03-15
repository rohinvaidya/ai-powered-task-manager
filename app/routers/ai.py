from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskResponse
from app.services.ai_service import get_ai_priority_suggestions

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/projects/{project_id}/suggest-priorities")
async def suggest_priorities(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Use Claude AI to analyze tasks in a project and suggest priorities.
    Returns suggestions, groupings (do today / this week / backlog), and a summary.
    """
    # Verify project ownership
    proj = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.owner_id == current_user.id
        )
    )
    if not proj.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch tasks
    result = await db.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = result.scalars().all()

    if not tasks:
        return {"message": "No tasks found in this project", "suggestions": []}

    # Serialize for AI
    task_dicts = [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status.value,
            "priority": t.priority.value,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "description": t.description or "",
        }
        for t in tasks
    ]

    suggestions = await get_ai_priority_suggestions(task_dicts)
    return suggestions


@router.post("/projects/{project_id}/apply-suggestions")
async def apply_ai_suggestions(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get AI suggestions AND automatically apply them to the tasks.
    Returns the updated tasks.
    """
    from app.models.task import TaskPriority

    proj = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.owner_id == current_user.id
        )
    )
    if not proj.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = result.scalars().all()

    task_dicts = [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status.value,
            "priority": t.priority.value,
            "due_date": t.due_date.isoformat() if t.due_date else None,
        }
        for t in tasks
    ]

    suggestions = await get_ai_priority_suggestions(task_dicts)

    # Build lookup
    task_map = {t.id: t for t in tasks}
    applied = 0

    for suggestion in suggestions.get("suggestions", []):
        task = task_map.get(suggestion["task_id"])
        if task:
            try:
                task.priority = TaskPriority(suggestion["suggested_priority"])
                applied += 1
            except ValueError:
                pass

    await db.commit()

    return {
        "applied": applied,
        "summary": suggestions.get("summary", ""),
        "groups": suggestions.get("groups", {}),
    }
