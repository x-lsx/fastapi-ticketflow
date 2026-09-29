from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EventStatus, SeatStatus

from .models import Event, EventZone, EventZoneSeat


class EventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, event_id: int) -> Event | None:
        return await self.db.get(Event, event_id)

    async def list_events(
        self,
        venue_id: int | None = None,
        category_id: int | None = None,
        status: EventStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Event], int]:
        query = select(Event)

        if venue_id is not None:
            query = query.where(Event.venue_id == venue_id)
        if category_id is not None:
            query = query.where(Event.category_id == category_id)
        if status is not None:
            query = query.where(Event.status == status)
        if date_from is not None:
            query = query.where(Event.start_at >= date_from)
        if date_to is not None:
            query = query.where(Event.start_at <= date_to)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar_one()

        query = query.order_by(Event.start_at).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def create(self, data: dict) -> Event:
        event = Event(**data)
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def update(self, event_id: int, data: dict) -> Event | None:
        event = await self.get_by_id(event_id)
        if not event:
            return None
        for key, value in data.items():
            setattr(event, key, value)
        await self.db.flush()
        await self.db.refresh(event)
        return event


class EventZoneRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, zone_id: int) -> EventZone | None:
        return await self.db.get(EventZone, zone_id)

    async def list_by_event_id(self, event_id: int) -> list[EventZone]:
        query = select(EventZone).where(EventZone.event_id == event_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: dict) -> EventZone:
        zone = EventZone(**data)
        self.db.add(zone)
        await self.db.flush()
        await self.db.refresh(zone)
        return zone

    async def update(self, zone_id: int, data: dict) -> EventZone | None:
        zone = await self.get_by_id(zone_id)
        if not zone:
            return None
        for key, value in data.items():
            setattr(zone, key, value)
        await self.db.flush()
        await self.db.refresh(zone)
        return zone


class EventZoneSeatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, seat_id: int) -> EventZoneSeat | None:
        return await self.db.get(EventZoneSeat, seat_id)

    async def list_by_event_zone_id(self, event_zone_id: int) -> list[EventZoneSeat]:
        query = select(EventZoneSeat).where(EventZoneSeat.event_zone_id == event_zone_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: dict) -> EventZoneSeat:
        seat = EventZoneSeat(**data)
        self.db.add(seat)
        await self.db.flush()
        await self.db.refresh(seat)
        return seat

    async def update(self, seat_id: int, data: dict) -> EventZoneSeat | None:
        seat = await self.get_by_id(seat_id)
        if not seat:
            return None
        for key, value in data.items():
            setattr(seat, key, value)
        await self.db.flush()
        await self.db.refresh(seat)
        return seat

    async def bulk_create(self, seats: list[dict]) -> list[EventZoneSeat]:
        """Bulk-вставка мест без N отдельных INSERT-ов."""
        objects = [EventZoneSeat(**s) for s in seats]
        self.db.add_all(objects)
        await self.db.flush()
        for obj in objects:
            await self.db.refresh(obj)
        return objects

