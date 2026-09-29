from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import VenueStatus, VenueZoneType
from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class Venue(Base, TimestampMixin):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VenueStatus] = mapped_column(
        SAEnum(VenueStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=VenueStatus.DRAFT,
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    zones: Mapped[list["VenueZone"]] = relationship(
        "VenueZone",
        back_populates="venue",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, name={self.name}, status={self.status})>"

    def __str__(self) -> str:
        return self.name


class VenueZone(Base, TimestampMixin):
    __tablename__ = "venue_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[VenueZoneType] = mapped_column(
        SAEnum(VenueZoneType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    venue: Mapped["Venue"] = relationship("Venue", back_populates="zones")
    seats: Mapped[list["VenueZoneSeat"]] = relationship(
        "VenueZoneSeat",
        back_populates="zone",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<VenueZone(id={self.id}, name={self.name}, type={self.type})>"

    def __str__(self) -> str:
        return self.name


class VenueZoneSeat(Base):
    __tablename__ = "venue_zone_seats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    venue_zone_id: Mapped[int] = mapped_column(
        ForeignKey("venue_zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row: Mapped[str | None] = mapped_column(String(20), nullable=True)
    seat_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    zone: Mapped["VenueZone"] = relationship("VenueZone", back_populates="seats")

    def __repr__(self) -> str:
        return f"<VenueZoneSeat(id={self.id}, row={self.row}, seat_number={self.seat_number})>"