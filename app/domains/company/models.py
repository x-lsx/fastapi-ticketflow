from app.core.mixins import TimestampMixin
from app.db.postgres import Base
# from app.domains.user.models import User
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), on_delete="CASCADE")
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(132), nullable=False, unique=True)

    owner: Mapped["User"] = relationship("User", back_populates="companies")

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, slug={self.slug})>"

    def __str__(self) -> str:
        return f"{self.slug}"
