from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_optional_user
from app.core.pagination import PaginatedResponse
from app.db.postgres import get_db
from app.domains.user.models import User

from .exceptions import (
    AlreadyOwner,
    CompanyAlreadyExists,
    CompanyNotFound,
    CompanyOwnerNotFound,
    TransferTargetNotMember,
)
from .schemas import (
    CompanyCreate,
    CompanyMemberResponse,
    CompanyResponse,
    CompanyUpdate,
    TransferOwnershipRequest,
)
from .service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


# ---------------------------------------------------------------------------
# Утилита: маппинг доменных исключений → HTTPException
# ---------------------------------------------------------------------------

def _map_exc(exc: Exception) -> HTTPException:
    if isinstance(exc, CompanyNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, CompanyAlreadyExists):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, (CompanyOwnerNotFound, TransferTargetNotMember)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, AlreadyOwner):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await CompanyService(db).create_company(data, user_id=current_user.id)
    except CompanyAlreadyExists as exc:
        raise _map_exc(exc)


@router.get("/", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
    search: str | None = Query(default=None),
    my: bool = Query(default=False, description="Только компании текущего пользователя"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    if my and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to filter by your companies",
            headers={"WWW-Authenticate": "Bearer"},
        )
    member_user_id = current_user.id if my else None
    return await CompanyService(db).list_companies(
        search=search,
        member_user_id=member_user_id,
        page=page,
        size=size,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await CompanyService(db).get_company(company_id)
    except CompanyNotFound as exc:
        raise _map_exc(exc)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await CompanyService(db).update_company(company_id, data)
    except CompanyNotFound as exc:
        raise _map_exc(exc)


@router.post(
    "/{company_id}/transfer-owner",
    response_model=CompanyMemberResponse,
    summary="Передать владение компанией другому участнику",
)
async def transfer_ownership(
    company_id: int,
    body: TransferOwnershipRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await CompanyService(db).transfer_ownership(
            company_id=company_id,
            from_user_id=current_user.id,
            to_user_id=body.to_user_id,
        )
    except (
        CompanyNotFound,
        CompanyOwnerNotFound,
        TransferTargetNotMember,
        AlreadyOwner,
    ) as exc:
        raise _map_exc(exc)
