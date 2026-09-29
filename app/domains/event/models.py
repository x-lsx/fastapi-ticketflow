from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EventStatus, SeatStatus
from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    organizer_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[EventStatus] = mapped_column(
        SAEnum(EventStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EventStatus.DRAFT,
    )

    # Relationships
    event_genres: Mapped[list["EventGenre"]] = relationship(  # noqa: F821
        "EventGenre",
        back_populates="event",
        passive_deletes=True,
    )
    zones: Mapped[list["EventZone"]] = relationship(
        "EventZone",
        back_populates="event",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, name={self.name}, status={self.status})>"

    def __str__(self) -> str:
        return self.name


class EventZone(Base, TimestampMixin):
    __tablename__ = "event_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    venue_zone_id: Mapped[int] = mapped_column(
        ForeignKey("venue_zones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="zones")
    seats: Mapped[list["EventZoneSeat"]] = relationship(
        "EventZoneSeat",
        back_populates="zone",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<EventZone(id={self.id}, event_id={self.event_id}, price={self.price})>"


class EventZoneSeat(Base):
    __tablename__ = "event_zone_seats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    event_zone_id: Mapped[int] = mapped_column(
        ForeignKey("event_zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    venue_zone_seat_id: Mapped[int | None] = mapped_column(
        ForeignKey("venue_zone_seats.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    row: Mapped[str | None] = mapped_column(String(20), nullable=True)
    seat_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[SeatStatus] = mapped_column(
        SAEnum(SeatStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SeatStatus.AVAILABLE,
    )

    # Relationships
    zone: Mapped["EventZone"] = relationship("EventZone", back_populates="seats")

    def __repr__(self) -> str:
        return (
            f"<EventZoneSeat(id={self.id}, row={self.row}, "
            f"seat_number={self.seat_number}, status={self.status})>"
        )


# Circular import resolved: EventGenre lives in catalog, but needs Event.
# We import it here so SQLAlchemy can resolve the relationship string "EventGenre".
from app.domains.catalog.models import EventGenre  # noqa: E402, F401