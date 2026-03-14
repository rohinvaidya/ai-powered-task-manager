from datetime import datetime

from pydantic import BaseModel

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    assignee_id: str | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assignee_id: str | None = None


class TaskResponse(TaskBase):
    id: str
    project_id: str
    order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
