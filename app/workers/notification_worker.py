"""
Notification worker — sends email/webhook notifications for task events.
Events: overdue, due_soon, status_changed, assigned
"""
import logging

from app.core.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.notification_worker.send_task_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_task_notification(
    self,
    task_id: str,
    task_title: str,
    event: str,
    assignee_id: str | None = None,
    extra: dict | None = None,
) -> dict:
    """
    Send a notification for a task event.
    Falls back to logging if email is not configured.
    """
    try:
        message = _build_message(task_title, event, extra or {})

        if _email_configured():
            import asyncio
            asyncio.run(_send_email_async(task_id, task_title, event, message))
        else:
            # Log to stdout when email is not configured (dev mode)
            logger.info(
                f"[NOTIFICATION] event={event} task_id={task_id} "
                f"assignee={assignee_id} | {message}"
            )

        return {"sent": True, "task_id": task_id, "event": event}

    except Exception as exc:
        logger.error(f"Notification failed for task {task_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.notification_worker.send_status_change_notification")
def send_status_change_notification(
    task_id: str,
    task_title: str,
    old_status: str,
    new_status: str,
    assignee_id: str | None = None,
) -> dict:
    """Triggered when a task status changes."""
    return send_task_notification.delay(
        task_id=task_id,
        task_title=task_title,
        event="status_changed",
        assignee_id=assignee_id,
        extra={"old_status": old_status, "new_status": new_status},
    ).get(timeout=10)


def _build_message(task_title: str, event: str, extra: dict) -> str:
    messages = {
        "overdue": f"Task '{task_title}' is overdue.",
        "due_soon": f"Task '{task_title}' is due soon.",
        "status_changed": (
            f"Task '{task_title}' status changed "
            f"from {extra.get('old_status')} to {extra.get('new_status')}."
        ),
        "assigned": f"You have been assigned to task '{task_title}'.",
    }
    return messages.get(event, f"Update on task '{task_title}': {event}")


def _email_configured() -> bool:
    return bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD)


async def _send_email_async(
    task_id: str, task_title: str, event: str, message: str
) -> None:
    """Send email using fastapi-mail when credentials are configured."""
    from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
    )

    msg = MessageSchema(
        subject=f"[Task Manager] {event.replace('_', ' ').title()}: {task_title}",
        recipients=[settings.MAIL_FROM],  # Replace with actual user email lookup
        body=message,
        subtype=MessageType.plain,
    )

    fm = FastMail(conf)
    await fm.send_message(msg)
    logger.info(f"Email sent for task {task_id} event={event}")
