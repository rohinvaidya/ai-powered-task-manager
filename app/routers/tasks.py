from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.redis import cache_delete_pattern, cache_get, cache_set
from app.models.project import Project
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])

CACHE_TTL = 300


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user.id)
    task = Task(**payload.model_dump(), project_id=project_id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    await cache_delete_pattern(f"tasks:{project_id}:*")
    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    project_id: str,
    status: TaskStatus | None = Query(None),
    priority: TaskPriority | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user.id)

    cache_key = f"tasks:{project_id}:list:{status}:{priority}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    query = select(Task).where(Task.project_id == project_id)
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    query = query.order_by(Task.order, Task.created_at)

    result = await db.execute(query)
    tasks = result.scalars().all()
    data = [TaskResponse.model_validate(t).model_dump(mode="json") for t in tasks]
    await cache_set(cache_key, data, ttl=CACHE_TTL)
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    project_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user.id)
    return await _get_task_or_404(db, task_id, project_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    project_id: str,
    task_id: str,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user.id)
    task = await _get_task_or_404(db, task_id, project_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    await cache_delete_pattern(f"tasks:{project_id}:*")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _assert_project_access(db, project_id, current_user.id)
    task = await _get_task_or_404(db, task_id, project_id)
    await db.delete(task)
    await db.commit()
    await cache_delete_pattern(f"tasks:{project_id}:*")


async def _assert_project_access(db: AsyncSession, project_id: str, owner_id: str) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _get_task_or_404(db: AsyncSession, task_id: str, project_id: str) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.project_id == project_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
