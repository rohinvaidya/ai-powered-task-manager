"""
Reminder worker — checks for overdue tasks and triggers notifications.
Run with: celery -A app.core.celery_app worker --loglevel=info
Schedule with: celery -A app.core.celery_app beat --loglevel=info
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.task import Task, TaskStatus
from app.workers.notification_worker import send_task_notification

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.reminder_worker.check_overdue_tasks")
def check_overdue_tasks() -> dict:
    """Scan for tasks past their due date and queue notifications."""
    import asyncio
    return asyncio.run(_check_overdue_tasks_async())


async def _check_overdue_tasks_async() -> dict:
    now = datetime.now(timezone.utc)
    notified = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task).where(
                Task.due_date < now,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
            )
        )
        overdue_tasks = result.scalars().all()

        for task in overdue_tasks:
            send_task_notification.delay(
                task_id=task.id,
                task_title=task.title,
                event="overdue",
                assignee_id=task.assignee_id,
            )
            notified += 1
            logger.info(f"Queued overdue notification for task {task.id}: {task.title}")

    return {"checked": True, "notified": notified}


@celery_app.task(name="app.workers.reminder_worker.send_due_soon_reminders")
def send_due_soon_reminders(hours_ahead: int = 24) -> dict:
    """Notify assignees of tasks due within the next N hours."""
    import asyncio
    return asyncio.run(_send_due_soon_async(hours_ahead))


async def _send_due_soon_async(hours_ahead: int) -> dict:
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=hours_ahead)
    notified = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task).where(
                Task.due_date >= now,
                Task.due_date <= cutoff,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
            )
        )
        upcoming = result.scalars().all()

        for task in upcoming:
            send_task_notification.delay(
                task_id=task.id,
                task_title=task.title,
                event="due_soon",
                assignee_id=task.assignee_id,
            )
            notified += 1

    return {"notified": notified, "hours_ahead": hours_ahead}
