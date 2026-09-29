from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SeatStatus, VenueZoneType

from .exceptions import (
    CapacityRequiredForStanding,
    EventNotFound,
    SeatedZoneHasNoSeats,
)
from .models import Event, EventZone
from .repository import EventRepository, EventZoneRepository, EventZoneSeatRepository
from .schemas import EventCreate, EventResponse, EventUpdate, EventZoneResponse


# ---------------------------------------------------------------------------
# EventService
# ---------------------------------------------------------------------------


class EventService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = EventRepository(db)
        self.db = db

    async def _get_or_404(self, event_id: int) -> Event:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise EventNotFound(f"Event {event_id} not found")
        return event

    async def get_event(self, event_id: int) -> EventResponse:
        event = await self._get_or_404(event_id)
        return EventResponse.model_validate(event)

    async def create_event(self, data: EventCreate) -> EventResponse:
        event = await self.repo.create(data.model_dump())
        await self.db.commit()
        return EventResponse.model_validate(event)

    async def update_event(self, event_id: int, data: EventUpdate) -> EventResponse:
        await self._get_or_404(event_id)
        updated = await self.repo.update(event_id, data.model_dump(exclude_unset=True))
        await self.db.commit()
        return EventResponse.model_validate(updated)


# ---------------------------------------------------------------------------
# EventZoneService
# ---------------------------------------------------------------------------


class EventZoneService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = EventZoneRepository(db)
        self.seat_repo = EventZoneSeatRepository(db)
        self.db = db

    async def _get_or_404(self, zone_id: int) -> EventZone:
        zone = await self.repo.get_by_id(zone_id)
        if not zone:
            from .exceptions import EventNotFound
            raise EventNotFound(f"EventZone {zone_id} not found")
        return zone

    async def get_event_zone(self, event_id: int, zone_id: int) -> EventZoneResponse:
        zone = await self._get_or_404(zone_id)
        if zone.event_id != event_id:
            from .exceptions import EventNotFound
            raise EventNotFound(f"EventZone {zone_id} not found in Event {event_id}")
        return EventZoneResponse.model_validate(zone)

    async def list_event_zones(self, event_id: int) -> list[EventZoneResponse]:
        zones = await self.repo.list_by_event_id(event_id)
        return [EventZoneResponse.model_validate(z) for z in zones]

    async def create_event_zone(
        self,
        event_id: int,
        venue_zone_id: int,
        price: Decimal,
        capacity: int | None = None,
    ) -> EventZoneResponse:
        """Создаёт EventZone и автоматически генерирует EventZoneSeat.

        Для seated-зон:
            - Читает VenueZoneSeat этой зоны.
            - Bulk-создаёт EventZoneSeat 1:1 (копирует row/seat_number,
              проставляет venue_zone_seat_id, status=available).
            - EventZone.capacity = количество созданных мест.
            - Если у зоны нет ни одного места — бросает SeatedZoneHasNoSeats.

        Для standing-зон:
            - capacity обязателен, иначе CapacityRequiredForStanding.
            - Bulk-создаёт capacity строк EventZoneSeat без номеров/рядов.

        Всё выполняется в одной транзакции (flush внутри, commit в конце).
        При любом исключении AsyncSession откатит транзакцию автоматически.

        Raises:
            EventNotFound: мероприятие не найдено.
            VenueZoneNotFound: зона площадки не найдена (из venue-домена).
            CapacityRequiredForStanding: capacity не передан для standing-зоны.
            SeatedZoneHasNoSeats: seated-зона не имеет мест в VenueZoneSeat.
        """
        # Отложенные импорты во избежание циклов на уровне модулей
        from app.domains.venue.exceptions import VenueZoneNotFound
        from app.domains.venue.models import VenueZone, VenueZoneSeat
        from app.domains.venue.repository import (
            VenueZoneSeatRepository,
            VenueZoneRepository,
        )

        # 1. Проверяем существование мероприятия
        event_repo = EventRepository(self.db)
        event = await event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFound(f"Event {event_id} not found")

        # 2. Проверяем существование зоны площадки
        zone_repo = VenueZoneRepository(self.db)
        venue_zone: VenueZone | None = await zone_repo.get_by_id(venue_zone_id)
        if not venue_zone:
            raise VenueZoneNotFound(f"VenueZone {venue_zone_id} not found")

        # 3. Для standing — capacity обязателен
        if venue_zone.type == VenueZoneType.STANDING and capacity is None:
            raise CapacityRequiredForStanding(
                "capacity is required when creating an event zone for a standing venue zone"
            )

        # 4. Определяем итоговую вместимость и собираем payloads для мест
        seat_payloads: list[dict] = []

        if venue_zone.type == VenueZoneType.SEATED:
            venue_seat_repo = VenueZoneSeatRepository(self.db)
            venue_seats: list[VenueZoneSeat] = await venue_seat_repo.get_by_zone_id(venue_zone_id)

            if not venue_seats:
                raise SeatedZoneHasNoSeats(
                    f"VenueZone {venue_zone_id} has no seats. "
                    "Run generate_seats first."
                )

            final_capacity = len(venue_seats)
            for vs in venue_seats:
                seat_payloads.append(
                    {
                        "venue_zone_seat_id": vs.id,
                        "row": vs.row,
                        "seat_number": vs.seat_number,
                        "status": SeatStatus.AVAILABLE,
                    }
                )
        else:
            # standing
            final_capacity = capacity  # type: ignore[assignment]
            for _ in range(final_capacity):
                seat_payloads.append(
                    {
                        "venue_zone_seat_id": None,
                        "row": None,
                        "seat_number": None,
                        "status": SeatStatus.AVAILABLE,
                    }
                )

        # 5. Создаём EventZone (flush — получаем id)
        event_zone: EventZone = await self.repo.create(
            {
                "event_id": event_id,
                "venue_zone_id": venue_zone_id,
                "price": price,
                "capacity": final_capacity,
            }
        )

        # 6. Проставляем event_zone_id в каждый payload и bulk-создаём места
        for payload in seat_payloads:
            payload["event_zone_id"] = event_zone.id

        await self.seat_repo.bulk_create(seat_payloads)

        # 7. Коммитим всю транзакцию
        await self.db.commit()

        return EventZoneResponse.model_validate(event_zone)
