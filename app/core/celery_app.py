from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "taskmanager",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.reminder_worker",
        "app.workers.notification_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # Check for overdue tasks every 5 minutes
        "check-overdue-tasks": {
            "task": "app.workers.reminder_worker.check_overdue_tasks",
            "schedule": 300.0,
        },
    },
)
