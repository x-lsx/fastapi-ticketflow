from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import VenueStatus

from .models import Venue, VenueZone, VenueZoneSeat


class VenueRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, venue_id: int) -> Venue | None:
        return await self.db.get(Venue, venue_id)

    async def list_venues(
        self,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
        status: VenueStatus | None = None,
        city: str | None = None,
    ) -> tuple[list[Venue], int]:
        query = select(Venue)
        if search:
            query = query.where(Venue.name.ilike(f"%{search}%"))
        if status:
            query = query.where(Venue.status == status)
        if city:
            query = query.where(Venue.city.ilike(f"%{city}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar_one()

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def create(self, data: dict) -> Venue:
        venue = Venue(**data)
        self.db.add(venue)
        await self.db.flush()
        await self.db.refresh(venue)
        return venue

    async def update(self, venue_id: int, data: dict) -> Venue | None:
        venue = await self.get_by_id(venue_id)
        if not venue:
            return None
        for key, value in data.items():
            setattr(venue, key, value)
        await self.db.flush()
        await self.db.refresh(venue)
        return venue

    async def delete(self, venue_id: int) -> bool:
        venue = await self.get_by_id(venue_id)
        if not venue:
            return False
        await self.db.delete(venue)
        await self.db.flush()
        return True


class VenueZoneRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, zone_id: int) -> VenueZone | None:
        return await self.db.get(VenueZone, zone_id)

    async def get_by_venue_id(self, venue_id: int) -> list[VenueZone]:
        query = select(VenueZone).where(VenueZone.venue_id == venue_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: dict) -> VenueZone:
        zone = VenueZone(**data)
        self.db.add(zone)
        await self.db.flush()
        await self.db.refresh(zone)
        return zone

    async def update(self, zone_id: int, data: dict) -> VenueZone | None:
        zone = await self.get_by_id(zone_id)
        if not zone:
            return None
        for key, value in data.items():
            setattr(zone, key, value)
        await self.db.flush()
        await self.db.refresh(zone)
        return zone

    async def delete(self, zone_id: int) -> bool:
        zone = await self.get_by_id(zone_id)
        if not zone:
            return False
        await self.db.delete(zone)
        await self.db.flush()
        return True


class VenueZoneSeatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, seat_id: int) -> VenueZoneSeat | None:
        return await self.db.get(VenueZoneSeat, seat_id)

    async def get_by_zone_id(self, zone_id: int) -> list[VenueZoneSeat]:
        query = select(VenueZoneSeat).where(VenueZoneSeat.venue_zone_id == zone_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: dict) -> VenueZoneSeat:
        seat = VenueZoneSeat(**data)
        self.db.add(seat)
        await self.db.flush()
        await self.db.refresh(seat)
        return seat

    async def bulk_create(self, seats: list[dict]) -> list[VenueZoneSeat]:
        objects = [VenueZoneSeat(**s) for s in seats]
        self.db.add_all(objects)
        await self.db.flush()
        for obj in objects:
            await self.db.refresh(obj)
        return objects

    async def delete(self, seat_id: int) -> bool:
        seat = await self.get_by_id(seat_id)
        if not seat:
            return False
        await self.db.delete(seat)
        await self.db.flush()
        return True

    async def delete_by_zone_id(self, zone_id: int) -> None:
        """Bulk-удаление всех мест зоны без загрузки объектов."""
        query = delete(VenueZoneSeat).where(VenueZoneSeat.venue_zone_id == zone_id)
        await self.db.execute(query)
        await self.db.flush()
