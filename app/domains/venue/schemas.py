from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import VenueStatus, VenueZoneType

# ---------------------------------------------------------------------------
# Venue
# ---------------------------------------------------------------------------


class VenueCreate(BaseModel):
    name: str = Field(..., max_length=200, description="Название площадки.")
    city: str = Field(..., max_length=100, description="Город.")
    address: str = Field(..., max_length=255, description="Адрес (улица, дом).")
    lat: float | None = Field(None, description="Широта.")
    lon: float | None = Field(None, description="Долгота.")
    map_url: str | None = Field(None, description="Ссылка на карту.")
    status: VenueStatus = Field(VenueStatus.DRAFT, description="Статус площадки.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Олимпийский",
                "city": "Москва",
                "address": "Олимпийский просп., 16",
                "lat": 55.7704,
                "lon": 37.6192,
                "map_url": "https://yandex.ru/maps/?ll=37.6192,55.7704",
                "status": "draft",
            }
        }
    )


class VenueUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    city: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=255)
    lat: float | None = None
    lon: float | None = None
    map_url: str | None = None
    status: VenueStatus | None = None


class VenueResponse(BaseModel):
    id: int
    name: str
    city: str
    address: str
    lat: float | None
    lon: float | None
    map_url: str | None
    status: VenueStatus
    created_by: int | None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# VenueZone
# ---------------------------------------------------------------------------


class VenueZoneCreate(BaseModel):
    name: str = Field(..., max_length=100, description="Название зоны.")
    type: VenueZoneType = Field(..., description="Тип зоны.")
    capacity: int = Field(..., gt=0, description="Вместимость.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Партер",
                "type": "seated",
                "capacity": 500,
            }
        }
    )


class VenueZoneUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    type: VenueZoneType | None = None
    capacity: int | None = Field(None, gt=0)


class VenueZoneResponse(BaseModel):
    id: int
    name: str
    venue_id: int
    type: VenueZoneType
    capacity: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# VenueZoneSeat
# ---------------------------------------------------------------------------


class VenueZoneSeatCreate(BaseModel):
    name: str | None = Field(None, max_length=50, description="Отображаемое имя места.")
    row: str | None = Field(None, max_length=20, description="Ряд.")
    seat_number: str | None = Field(None, max_length=20, description="Номер места.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "row": "A",
                "seat_number": "12",
            }
        }
    )


class VenueZoneSeatResponse(BaseModel):
    id: int
    name: str | None
    venue_zone_id: int
    row: str | None
    seat_number: str | None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# generate_seats helpers
# ---------------------------------------------------------------------------


class RowLayout(BaseModel):
    """Описание одного ряда для bulk-генерации мест."""

    row: str = Field(..., max_length=20, description="Название ряда (например, 'A', '1').")
    seats_count: int = Field(..., gt=0, description="Количество мест в ряду.")


class GenerateSeatsRequest(BaseModel):
    """Тело запроса для generate_seats."""

    layout: list[RowLayout] = Field(..., min_length=1, description="Список рядов с количеством мест.")
    replace: bool = Field(False, description="При True удаляет существующие места перед генерацией.")

