from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_session
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserRead
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])


def get_user_repo(session: AsyncSession = Depends(get_session)) -> BaseRepository[User]:
    return BaseRepository(User, session)


@router.get("/", response_model=list[UserRead])
async def list_users(repo: BaseRepository[User] = Depends(get_user_repo)):
    users, _ = await repo.list_paginated()
    return users


@router.post("/", response_model=UserRead)
async def create_user(
    user_create: UserCreate, repo: BaseRepository[User] = Depends(get_user_repo)
):
    user = User(**user_create.model_dump())
    created_user = await repo.create(user)
    return created_user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, repo: BaseRepository[User] = Depends(get_user_repo)):
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
