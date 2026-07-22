from fastapi import APIRouter, Depends

from app.api.v1.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserRead


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "/me",
    response_model=UserRead,
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user
