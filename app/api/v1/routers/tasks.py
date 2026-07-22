from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.core.database import get_session
from app.models.task import Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate, TaskRead

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(get_current_user)],
)


def get_task_repo(session: AsyncSession = Depends(get_session)) -> BaseRepository[Task]:
    return BaseRepository(Task, session)


async def get_task_or_404(
    task_id: int, repo: BaseRepository[Task] = Depends(get_task_repo)
) -> Task:
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/", response_model=list[TaskRead])
async def list_tasks(repo: BaseRepository[Task] = Depends(get_task_repo)):
    tasks, _ = await repo.list_paginated()
    return tasks


@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate, repo: BaseRepository[Task] = Depends(get_task_repo)
):
    task = Task(**payload.model_dump())
    try:
        return await repo.create(task)
    except IntegrityError:
        await repo.session.rollback()
        raise HTTPException(
            status_code=400, detail="project_id or assignee_id không tồn tại"
        )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task: Task = Depends(get_task_or_404)):
    return task


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    payload: TaskCreate,
    task: Task = Depends(get_task_or_404),
    repo: BaseRepository[Task] = Depends(get_task_repo),
):
    for field, value in payload.model_dump().items():
        setattr(task, field, value)
    updated_task = await repo.update(task)
    return updated_task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task: Task = Depends(get_task_or_404),
    repo: BaseRepository[Task] = Depends(get_task_repo),
):
    await repo.delete(task)
