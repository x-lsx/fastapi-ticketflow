from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import EventStatus, SeatStatus


# ── Event ──────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    name: str = Field(..., max_length=200, description="Название мероприятия")
    organizer_id: int = Field(..., description="ID компании-организатора")
    category_id: int = Field(..., description="ID категории")
    venue_id: int = Field(..., description="ID площадки")
    start_at: datetime = Field(..., description="Дата и время начала")
    end_at: datetime | None = Field(None, description="Дата и время окончания")
    image_url: str | None = Field(None, description="URL обложки")
    status: EventStatus = Field(EventStatus.DRAFT, description="Статус мероприятия")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Rock Night 2026",
                "organizer_id": 1,
                "category_id": 2,
                "venue_id": 3,
                "start_at": "2026-11-01T20:00:00+05:00",
                "end_at": "2026-11-01T23:00:00+05:00",
                "image_url": "https://cdn.example.com/rock.jpg",
                "status": "draft",
            }
        }
    )


class EventUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    category_id: int | None = None
    venue_id: int | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    image_url: str | None = None
    status: EventStatus | None = None


class EventResponse(BaseModel):
    id: int
    name: str
    organizer_id: int
    category_id: int
    venue_id: int
    start_at: datetime
    end_at: datetime | None
    image_url: str | None
    status: EventStatus

    model_config = ConfigDict(from_attributes=True)




# ── EventZone ──────────────────────────────────────────────────────────────

class EventZoneCreate(BaseModel):
    venue_zone_id: int = Field(..., description="ID зоны площадки")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Цена билета")
    capacity: int | None = Field(
        None,
        gt=0,
        description=(
            "Обязателен для standing-зон. "
            "Для seated игнорируется — берётся из количества VenueZoneSeat."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "venue_zone_id": 4,
                "price": "1500.00",
                "capacity": None,
            }
        }
    )


class EventZoneUpdate(BaseModel):
    price: Decimal | None = Field(None, ge=0, decimal_places=2)
    capacity: int | None = Field(None, gt=0)


class EventZoneResponse(BaseModel):
    id: int
    event_id: int
    venue_zone_id: int
    price: Decimal
    capacity: int

    model_config = ConfigDict(from_attributes=True)


# ── EventZoneSeat ──────────────────────────────────────────────────────────

class EventZoneSeatCreate(BaseModel):
    event_zone_id: int = Field(..., description="ID зоны мероприятия")
    venue_zone_seat_id: int | None = Field(None, description="ID места площадки (null для standing)")
    row: str | None = Field(None, max_length=20, description="Ряд")
    seat_number: str | None = Field(None, max_length=20, description="Номер места")
    status: SeatStatus = Field(SeatStatus.AVAILABLE, description="Статус места")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_zone_id": 5,
                "venue_zone_seat_id": 12,
                "row": "A",
                "seat_number": "7",
                "status": "available",
            }
        }
    )


class EventZoneSeatUpdate(BaseModel):
    status: SeatStatus | None = None
    row: str | None = Field(None, max_length=20)
    seat_number: str | None = Field(None, max_length=20)


class EventZoneSeatResponse(BaseModel):
    id: int
    event_zone_id: int
    venue_zone_seat_id: int | None
    row: str | None
    seat_number: str | None
    status: SeatStatus

    model_config = ConfigDict(from_attributes=True)
