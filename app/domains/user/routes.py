from app.core.dependencies import get_current_user
from app.db.postgres import get_db
from app.db.redis import get_redis
from fastapi import APIRouter, Depends, status
from fastapi.param_functions import Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .service import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"]
)


@router.get("/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
    ):
    service = UserService(db)
    return await service.get_user_by_id(user.id)