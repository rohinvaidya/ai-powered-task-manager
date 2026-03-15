"""
Analytics service — per-user and per-project task statistics.
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus


async def get_user_analytics(db: AsyncSession, user_id: str) -> dict:
    """Return task statistics for the current user across all their projects."""
    from app.models.project import Project

    # Get all project IDs owned by the user
    proj_result = await db.execute(
        select(Project.id).where(Project.owner_id == user_id)
    )
    project_ids = [row[0] for row in proj_result.all()]

    if not project_ids:
        return _empty_analytics()

    # Total tasks
    total = await _count(db, Task.project_id.in_(project_ids))

    # By status
    by_status = await _count_by(db, Task.status, Task.project_id.in_(project_ids))

    # By priority
    by_priority = await _count_by(db, Task.priority, Task.project_id.in_(project_ids))

    # Overdue
    now = datetime.now(timezone.utc)
    overdue = await _count(
        db,
        Task.project_id.in_(project_ids),
        Task.due_date < now,
        Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
    )

    # Completion rate
    done = by_status.get(TaskStatus.DONE, 0)
    completion_rate = round(done / total * 100, 1) if total > 0 else 0.0

    return {
        "total_tasks": total,
        "completion_rate_pct": completion_rate,
        "overdue_tasks": overdue,
        "by_status": {k.value: v for k, v in by_status.items()},
        "by_priority": {k.value: v for k, v in by_priority.items()},
        "project_count": len(project_ids),
    }


async def get_project_analytics(db: AsyncSession, project_id: str) -> dict:
    """Return task statistics for a specific project."""
    total = await _count(db, Task.project_id == project_id)
    by_status = await _count_by(db, Task.status, Task.project_id == project_id)

    now = datetime.now(timezone.utc)
    overdue = await _count(
        db,
        Task.project_id == project_id,
        Task.due_date < now,
        Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
    )

    done = by_status.get(TaskStatus.DONE, 0)
    completion_rate = round(done / total * 100, 1) if total > 0 else 0.0

    return {
        "project_id": project_id,
        "total_tasks": total,
        "completion_rate_pct": completion_rate,
        "overdue_tasks": overdue,
        "by_status": {k.value: v for k, v in by_status.items()},
    }


async def _count(db: AsyncSession, *conditions) -> int:
    result = await db.execute(select(func.count()).select_from(Task).where(*conditions))
    return result.scalar() or 0


async def _count_by(db: AsyncSession, column, *conditions) -> dict:
    result = await db.execute(
        select(column, func.count()).select_from(Task).where(*conditions).group_by(column)
    )
    return {row[0]: row[1] for row in result.all()}


def _empty_analytics() -> dict:
    return {
        "total_tasks": 0,
        "completion_rate_pct": 0.0,
        "overdue_tasks": 0,
        "by_status": {},
        "by_priority": {},
        "project_count": 0,
    }
