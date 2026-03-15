from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.analytics_service import get_project_analytics, get_user_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/me")
async def my_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return task analytics for the current user across all projects."""
    return await get_user_analytics(db, current_user.id)


@router.get("/projects/{project_id}")
async def project_analytics(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return task analytics for a specific project."""
    from sqlalchemy import select
    from app.models.project import Project
    from fastapi import HTTPException

    proj = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id,
        )
    )
    if not proj.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    return await get_project_analytics(db, project_id)
