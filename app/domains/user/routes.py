from fastapi import APIRouter, Depends, status
from fastapi.param_functions import Body, Query
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.redis import get_redis
from app.db.postgres import get_db
from app.core.dependencies import get_current_user
from .service import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"]
)


@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    return user
