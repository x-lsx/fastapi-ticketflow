from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db

from .exceptions import (
    CapacityRequiredForStanding,
    EventNotFound,
    SeatedZoneHasNoSeats,
)
from .schemas import (
    EventCreate,
    EventResponse,
    EventUpdate,
    EventZoneCreate,
    EventZoneResponse,
)
from .service import EventService, EventZoneService

router = APIRouter(prefix="/events", tags=["events"])


# ---------------------------------------------------------------------------
# Утилита: маппинг доменных исключений → HTTPException
# ---------------------------------------------------------------------------

def _map_exc(exc: Exception) -> HTTPException:
    if isinstance(exc, EventNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, SeatedZoneHasNoSeats):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, CapacityRequiredForStanding):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    # VenueZoneNotFound — cross-domain, импортируем лениво
    from app.domains.venue.exceptions import VenueZoneNotFound
    if isinstance(exc, VenueZoneNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Events — CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    return await EventService(db).create_event(data)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await EventService(db).get_event(event_id)
    except EventNotFound as exc:
        raise _map_exc(exc)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await EventService(db).update_event(event_id, data)
    except EventNotFound as exc:
        raise _map_exc(exc)


# ---------------------------------------------------------------------------
# Event Zones — /events/{event_id}/zones
# ---------------------------------------------------------------------------

@router.post(
    "/{event_id}/zones",
    response_model=EventZoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать зону мероприятия (+ автоматически все места)",
)
async def create_event_zone(
    event_id: int,
    data: EventZoneCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Атомарно создаёт `EventZone` и все `EventZoneSeat`:

    - **seated**: места копируются 1:1 из `VenueZoneSeat`. `capacity` в теле игнорируется.
    - **standing**: создаётся `capacity` мест без номеров. `capacity` обязателен.
    """
    try:
        return await EventZoneService(db).create_event_zone(
            event_id=event_id,
            venue_zone_id=data.venue_zone_id,
            price=data.price,
            capacity=data.capacity,
        )
    except (EventNotFound, SeatedZoneHasNoSeats, CapacityRequiredForStanding) as exc:
        raise _map_exc(exc)
    except Exception as exc:
        raise _map_exc(exc)


@router.get(
    "/{event_id}/zones",
    response_model=list[EventZoneResponse],
    summary="Список зон мероприятия",
)
async def list_event_zones(event_id: int, db: AsyncSession = Depends(get_db)):
    return await EventZoneService(db).list_event_zones(event_id)


@router.get(
    "/{event_id}/zones/{zone_id}",
    response_model=EventZoneResponse,
    summary="Получить зону мероприятия",
)
async def get_event_zone(event_id: int, zone_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await EventZoneService(db).get_event_zone(event_id, zone_id)
    except EventNotFound as exc:
        raise _map_exc(exc)
