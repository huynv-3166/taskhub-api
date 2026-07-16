from enum import Enum
from pydantic import BaseModel


class TaskStatus(str, Enum):
    DONE = "DONE"
    IN_PROGRESS = "IN_PROGRESS"
    TODO = "TODO"


class Task(BaseModel):
    id: int
    title: str
    status: TaskStatus


class TaskCreate(BaseModel):
    title: str
    status: TaskStatus
