import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EventStatus, VenueStatus, VenueZoneType
from app.core.pagination import PaginatedResponse

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
from .models import Venue, VenueZone, VenueZoneSeat
from .repository import VenueRepository, VenueZoneRepository, VenueZoneSeatRepository
from .schemas import (
    RowLayout,
    VenueCreate,
    VenueResponse,
    VenueUpdate,
    VenueZoneCreate,
    VenueZoneResponse,
    VenueZoneSeatCreate,
    VenueZoneSeatResponse,
    VenueZoneUpdate,
)

# ---------------------------------------------------------------------------
# VenueService
# ---------------------------------------------------------------------------


class VenueService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = VenueRepository(db)
        self.db = db

    async def _get_or_404(self, venue_id: int) -> Venue:
        venue = await self.repo.get_by_id(venue_id)
        if not venue:
            raise VenueNotFound(f"Venue {venue_id} not found")
        return venue

    async def _has_published_events(self, venue_id: int) -> bool:
        """Проверяем, есть ли опубликованные мероприятия на площадке."""
        # Импорт здесь, чтобы избежать циклических зависимостей на уровне модулей
        from app.domains.event.models import Event

        query = select(Event).where(
            Event.venue_id == venue_id,
            Event.status == EventStatus.PUBLISHED,
        ).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_venue(self, venue_id: int) -> VenueResponse:
        venue = await self._get_or_404(venue_id)
        return VenueResponse.model_validate(venue)

    async def list_venues(
        self,
        search: str | None = None,
        city: str | None = None,
        status: VenueStatus | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[VenueResponse]:
        offset = (page - 1) * size
        venues, total = await self.repo.list_venues(
            search=search,
            city=city,
            status=status,
            limit=size,
            offset=offset,
        )
        return PaginatedResponse(
            items=[VenueResponse.model_validate(v) for v in venues],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 1,
        )

    async def create_venue(self, data: VenueCreate, created_by: int) -> VenueResponse:
        payload = data.model_dump()
        payload["created_by"] = created_by
        venue = await self.repo.create(payload)
        await self.db.commit()
        return VenueResponse.model_validate(venue)

    async def update_venue(self, venue_id: int, data: VenueUpdate) -> VenueResponse:
        venue = await self._get_or_404(venue_id)

        # Бизнес-правило: нельзя архивировать, если есть published-события
        if data.status == VenueStatus.ARCHIVED and venue.status != VenueStatus.ARCHIVED:
            if await self._has_published_events(venue_id):
                raise VenueArchiveBlocked(
                    "Cannot archive venue: it has published events"
                )

        payload = data.model_dump(exclude_unset=True)
        updated = await self.repo.update(venue_id, payload)
        await self.db.commit()
        return VenueResponse.model_validate(updated)

    async def delete_venue(self, venue_id: int) -> None:
        venue = await self._get_or_404(venue_id)

        # Бизнес-правило: нельзя удалить активную площадку
        if venue.status == VenueStatus.ACTIVE:
            raise VenueDeleteBlocked(
                "Cannot delete an active venue. Archive it first."
            )

        await self.repo.delete(venue_id)
        await self.db.commit()


# ---------------------------------------------------------------------------
# VenueZoneService
# ---------------------------------------------------------------------------


class VenueZoneService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = VenueZoneRepository(db)
        self.venue_repo = VenueRepository(db)
        self.seat_repo = VenueZoneSeatRepository(db)
        self.db = db

    async def _get_or_404(self, zone_id: int) -> VenueZone:
        zone = await self.repo.get_by_id(zone_id)
        if not zone:
            raise VenueZoneNotFound(f"VenueZone {zone_id} not found")
        return zone

    async def _venue_or_404(self, venue_id: int) -> None:
        if not await self.venue_repo.get_by_id(venue_id):
            raise VenueNotFound(f"Venue {venue_id} not found")

    async def get_zone(self, zone_id: int) -> VenueZoneResponse:
        zone = await self._get_or_404(zone_id)
        return VenueZoneResponse.model_validate(zone)

    async def list_zones(self, venue_id: int) -> list[VenueZoneResponse]:
        await self._venue_or_404(venue_id)
        zones = await self.repo.get_by_venue_id(venue_id)
        return [VenueZoneResponse.model_validate(z) for z in zones]

    async def create_zone(self, venue_id: int, data: VenueZoneCreate) -> VenueZoneResponse:
        await self._venue_or_404(venue_id)
        payload = data.model_dump()
        payload["venue_id"] = venue_id
        zone = await self.repo.create(payload)
        await self.db.commit()
        return VenueZoneResponse.model_validate(zone)

    async def update_zone(self, zone_id: int, data: VenueZoneUpdate) -> VenueZoneResponse:
        zone = await self._get_or_404(zone_id)

        # Бизнес-правило: нельзя менять тип зоны, если уже есть места
        if data.type is not None and data.type != zone.type:
            seats = await self.seat_repo.get_by_zone_id(zone_id)
            if seats:
                raise ZoneTypeChangeBlocked(
                    "Cannot change zone type: zone already has seats"
                )

        payload = data.model_dump(exclude_unset=True)
        updated = await self.repo.update(zone_id, payload)
        await self.db.commit()
        return VenueZoneResponse.model_validate(updated)

    async def delete_zone(self, zone_id: int) -> None:
        await self._get_or_404(zone_id)
        await self.repo.delete(zone_id)
        await self.db.commit()


# ---------------------------------------------------------------------------
# VenueZoneSeatService
# ---------------------------------------------------------------------------


class VenueZoneSeatService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = VenueZoneSeatRepository(db)
        self.zone_repo = VenueZoneRepository(db)
        self.db = db

    async def _get_or_404(self, seat_id: int) -> VenueZoneSeat:
        seat = await self.repo.get_by_id(seat_id)
        if not seat:
            raise VenueZoneSeatNotFound(f"VenueZoneSeat {seat_id} not found")
        return seat

    async def _zone_or_404(self, zone_id: int) -> VenueZone:
        zone = await self.zone_repo.get_by_id(zone_id)
        if not zone:
            raise VenueZoneNotFound(f"VenueZone {zone_id} not found")
        return zone

    def _validate_seat_for_zone(self, zone: VenueZone, data: VenueZoneSeatCreate) -> None:
        """Для seated-зоны хотя бы одно из row/seat_number должно быть заполнено."""
        if zone.type == VenueZoneType.SEATED:
            if not data.row and not data.seat_number:
                raise SeatedSeatMissingNumber(
                    "Seated zone seats must have at least row or seat_number"
                )

    async def get_seat(self, seat_id: int) -> VenueZoneSeatResponse:
        seat = await self._get_or_404(seat_id)
        return VenueZoneSeatResponse.model_validate(seat)

    async def list_seats(self, zone_id: int) -> list[VenueZoneSeatResponse]:
        await self._zone_or_404(zone_id)
        seats = await self.repo.get_by_zone_id(zone_id)
        return [VenueZoneSeatResponse.model_validate(s) for s in seats]

    async def create_seat(self, zone_id: int, data: VenueZoneSeatCreate) -> VenueZoneSeatResponse:
        zone = await self._zone_or_404(zone_id)
        self._validate_seat_for_zone(zone, data)
        payload = data.model_dump()
        payload["venue_zone_id"] = zone_id
        seat = await self.repo.create(payload)
        await self.db.commit()
        return VenueZoneSeatResponse.model_validate(seat)

    async def bulk_create_seats(
        self, zone_id: int, seats_data: list[VenueZoneSeatCreate]
    ) -> list[VenueZoneSeatResponse]:
        zone = await self._zone_or_404(zone_id)
        for item in seats_data:
            self._validate_seat_for_zone(zone, item)
        payloads = [{**s.model_dump(), "venue_zone_id": zone_id} for s in seats_data]
        created = await self.repo.bulk_create(payloads)
        await self.db.commit()
        return [VenueZoneSeatResponse.model_validate(s) for s in created]

    async def delete_seat(self, seat_id: int) -> None:
        await self._get_or_404(seat_id)
        await self.repo.delete(seat_id)
        await self.db.commit()

    async def generate_seats(
        self,
        venue_zone_id: int,
        layout: list[RowLayout],
        replace: bool = False,
    ) -> list[VenueZoneSeatResponse]:
        """Bulk-генерация мест для seated-зоны по описанию рядов.

        Args:
            venue_zone_id: ID зоны площадки.
            layout: список рядов (row + seats_count).
            replace: если True — удалить существующие места перед генерацией.

        Raises:
            VenueZoneNotFound: зона не найдена.
            ZoneNotSeated: зона не является seated.
            SeatsAlreadyExist: места уже есть и replace=False.
            LayoutExceedsCapacity: суммарное кол-во мест в layout > zone.capacity.
        """
        zone = await self._zone_or_404(venue_zone_id)

        if zone.type != VenueZoneType.SEATED:
            raise ZoneNotSeated(
                f"VenueZone {venue_zone_id} has type '{zone.type.value}', "
                "generate_seats is only allowed for seated zones"
            )

        total_seats = sum(row.seats_count for row in layout)
        if total_seats > zone.capacity:
            raise LayoutExceedsCapacity(
                f"Layout produces {total_seats} seats, "
                f"but VenueZone {venue_zone_id} capacity is {zone.capacity}."
            )

        existing = await self.repo.get_by_zone_id(venue_zone_id)
        if existing:
            if not replace:
                raise SeatsAlreadyExist(
                    f"VenueZone {venue_zone_id} already has {len(existing)} seats. "
                    "Pass replace=True to overwrite."
                )
            await self.repo.delete_by_zone_id(venue_zone_id)

        payloads: list[dict] = []
        for row_def in layout:
            for seat_num in range(1, row_def.seats_count + 1):
                payloads.append(
                    {
                        "venue_zone_id": venue_zone_id,
                        "row": row_def.row,
                        "seat_number": str(seat_num),
                        "name": None,
                    }
                )

        created = await self.repo.bulk_create(payloads)
        await self.db.commit()
        return [VenueZoneSeatResponse.model_validate(s) for s in created]

