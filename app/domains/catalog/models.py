from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"

    def __str__(self) -> str:
        return self.name


class Genre(Base, TimestampMixin):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    event_genres: Mapped[list["EventGenre"]] = relationship(
        "EventGenre",
        back_populates="genre",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Genre(id={self.id}, name={self.name})>"

    def __str__(self) -> str:
        return self.name


class EventGenre(Base):
    __tablename__ = "event_genres"
    __table_args__ = (
        UniqueConstraint("event_id", "genre_id", name="uq_event_genres_event_genre"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    genre: Mapped["Genre"] = relationship("Genre", back_populates="event_genres")
    event: Mapped["Event"] = relationship("Event", back_populates="event_genres")

    def __repr__(self) -> str:
        return f"<EventGenre(id={self.id}, event_id={self.event_id}, genre_id={self.genre_id})>"
