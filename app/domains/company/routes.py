from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.db.postgres import get_db
from app.domains.user.models import User
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import CompanyCreate, CompanyResponse
from .service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company_service = CompanyService(db)
    return await company_service.create_company(company_data, current_user)


@router.get("/", response_model=PaginatedResponse[CompanyResponse])
async def get(
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=20),
):
    company_service = CompanyService(db)
    return await company_service.get_company_by_name(
        search=search,
        page=page,
        size=size,
    )
