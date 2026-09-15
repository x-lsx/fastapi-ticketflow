from app.core.mixins import TimestampMixin
from app.db.postgres import Base
# from app.domains.company.models import Company
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base, TimestampMixin):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(20), nullable=True)
    last_name: Mapped[str] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    companies: Mapped[list["Company"]] = relationship("Company", back_populates="owner")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, mail={self.email}, active={self.is_active})>"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} <{self.email}>"
