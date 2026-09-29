from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.enums import VenueStatus
from app.core.pagination import PaginatedResponse
from app.db.postgres import get_db
from app.domains.user.models import User

from .exceptions import (
    LayoutExceedsCapacity,
    SeatedSeatMissingNumber,
    SeatsAlreadyExist,
    VenueArchiveBlocked,
    VenueDeleteBlocked,
    VenueNotFound,
    VenueZoneNotFound,
    VenueZoneSeatNotFound,
    ZoneNotSeated,
    ZoneTypeChangeBlocked,
)
from .schemas import (
    GenerateSeatsRequest,
    VenueCreate,
    VenueResponse,
    VenueUpdate,
    VenueZoneCreate,
    VenueZoneResponse,
    VenueZoneSeatCreate,
    VenueZoneSeatResponse,
    VenueZoneUpdate,
)
from .service import VenueService, VenueZoneSeatService, VenueZoneService

router = APIRouter(prefix="/venues", tags=["venues"])


# ---------------------------------------------------------------------------
# Утилита: маппинг доменных исключений → HTTPException
# ---------------------------------------------------------------------------

def _map_exc(exc: Exception) -> HTTPException:
    if isinstance(exc, (VenueNotFound, VenueZoneNotFound, VenueZoneSeatNotFound)):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (VenueArchiveBlocked, VenueDeleteBlocked, ZoneTypeChangeBlocked,
                        ZoneNotSeated, SeatsAlreadyExist)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, (SeatedSeatMissingNumber, LayoutExceedsCapacity)):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    # Неожиданное доменное исключение
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Venues
# ---------------------------------------------------------------------------

@router.post("/", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
async def create_venue(
    data: VenueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await VenueService(db).create_venue(data, created_by=current_user.id)
    except (VenueNotFound,) as exc:
        raise _map_exc(exc)


@router.get("/", response_model=PaginatedResponse[VenueResponse])
async def list_venues(
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(default=None),
    city: str | None = Query(default=None),
    status_filter: VenueStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return await VenueService(db).list_venues(
        search=search,
        city=city,
        status=status_filter,
        page=page,
        size=size,
    )


@router.get("/{venue_id}", response_model=VenueResponse)
async def get_venue(venue_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await VenueService(db).get_venue(venue_id)
    except VenueNotFound as exc:
        raise _map_exc(exc)


@router.patch("/{venue_id}", response_model=VenueResponse)
async def update_venue(
    venue_id: int,
    data: VenueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await VenueService(db).update_venue(venue_id, data)
    except (VenueNotFound, VenueArchiveBlocked) as exc:
        raise _map_exc(exc)


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue(
    venue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await VenueService(db).delete_venue(venue_id)
    except (VenueNotFound, VenueDeleteBlocked) as exc:
        raise _map_exc(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Zones — /venues/{venue_id}/zones
# ---------------------------------------------------------------------------

@router.post(
    "/{venue_id}/zones",
    response_model=VenueZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_zone(
    venue_id: int,
    data: VenueZoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await VenueZoneService(db).create_zone(venue_id, data)
    except VenueNotFound as exc:
        raise _map_exc(exc)


@router.get("/{venue_id}/zones", response_model=list[VenueZoneResponse])
async def list_zones(venue_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await VenueZoneService(db).list_zones(venue_id)
    except VenueNotFound as exc:
        raise _map_exc(exc)


@router.get("/{venue_id}/zones/{zone_id}", response_model=VenueZoneResponse)
async def get_zone(venue_id: int, zone_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await VenueZoneService(db).get_zone(zone_id)
    except VenueZoneNotFound as exc:
        raise _map_exc(exc)


@router.patch("/{venue_id}/zones/{zone_id}", response_model=VenueZoneResponse)
async def update_zone(
    venue_id: int,
    zone_id: int,
    data: VenueZoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await VenueZoneService(db).update_zone(zone_id, data)
    except (VenueZoneNotFound, ZoneTypeChangeBlocked) as exc:
        raise _map_exc(exc)


@router.delete("/{venue_id}/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    venue_id: int,
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await VenueZoneService(db).delete_zone(zone_id)
    except VenueZoneNotFound as exc:
        raise _map_exc(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Seats — /venues/{venue_id}/zones/{zone_id}/seats
# ---------------------------------------------------------------------------

@router.post(
    "/{venue_id}/zones/{zone_id}/seats",
    response_model=VenueZoneSeatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_seat(
    venue_id: int,
    zone_id: int,
    data: VenueZoneSeatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await VenueZoneSeatService(db).create_seat(zone_id, data)
    except (VenueZoneNotFound, SeatedSeatMissingNumber) as exc:
        raise _map_exc(exc)


@router.post(
    "/{venue_id}/zones/{zone_id}/seats/bulk",
    response_model=list[VenueZoneSeatResponse],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_seats(
    venue_id: int,
    zone_id: int,
    seats: list[VenueZoneSeatCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await VenueZoneSeatService(db).bulk_create_seats(zone_id, seats)
    except (VenueZoneNotFound, SeatedSeatMissingNumber) as exc:
        raise _map_exc(exc)


@router.post(
    "/{venue_id}/zones/{zone_id}/seats/generate",
    response_model=list[VenueZoneSeatResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Сгенерировать места по рядам (только для seated-зон)",
)
async def generate_seats(
    venue_id: int,
    zone_id: int,
    data: GenerateSeatsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await VenueZoneSeatService(db).generate_seats(
            venue_zone_id=zone_id,
            layout=data.layout,
            replace=data.replace,
        )
    except (VenueZoneNotFound, ZoneNotSeated, SeatsAlreadyExist, LayoutExceedsCapacity) as exc:
        raise _map_exc(exc)


@router.get(
    "/{venue_id}/zones/{zone_id}/seats",
    response_model=list[VenueZoneSeatResponse],
)
async def list_seats(venue_id: int, zone_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await VenueZoneSeatService(db).list_seats(zone_id)
    except VenueZoneNotFound as exc:
        raise _map_exc(exc)


@router.delete(
    "/{venue_id}/zones/{zone_id}/seats/{seat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_seat(
    venue_id: int,
    zone_id: int,
    seat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await VenueZoneSeatService(db).delete_seat(seat_id)
    except VenueZoneSeatNotFound as exc:
        raise _map_exc(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
