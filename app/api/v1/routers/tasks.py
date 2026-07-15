from fastapi import APIRouter, Depends, HTTPException
from app.schemas.task import Task, TaskCreate

router = APIRouter(prefix="/tasks", tags=["tasks"])

MOCK_TASKS = [
    {"id": 1, "title": "DB design", "status": "DONE"},
    {"id": 2, "title": "API Login", "status": "IN_PROGRESS"},
    {"id": 3, "title": "Docker setup", "status": "TODO"},
]


def get_task(task_id: int) -> dict:
    for task in MOCK_TASKS:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


def get_next_task_id() -> int:
    return max(task["id"] for task in MOCK_TASKS) + 1


@router.get("/", response_model=list[Task])
async def get_tasks():
    return MOCK_TASKS


@router.get("/{task_id}", response_model=Task)
async def get_task_by_id(task: dict = Depends(get_task)):
    return task


@router.post("/", response_model=Task, status_code=201)
async def create_task(task: TaskCreate):
    new_task = {"id": get_next_task_id(), "title": task.title, "status": task.status}
    MOCK_TASKS.append(new_task)
    return new_task


@router.put("/{task_id}", response_model=Task)
async def update_task(payload: TaskCreate, task: dict = Depends(get_task)):
    task["title"] = payload.title
    task["status"] = payload.status
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task: dict = Depends(get_task)):
    MOCK_TASKS.remove(task)
    return None
