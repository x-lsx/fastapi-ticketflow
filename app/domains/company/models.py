from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.mixins import TimestampMixin
from app.db.postgres import Base


class RoleName(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    SCANNER = "scanner"


ROLE_PERMISSIONS: dict[RoleName, set[str]] = {
    RoleName.OWNER: {"event:create", "event:publish", "company:manage_members", "*"},
    RoleName.MANAGER: {"event:create", "event:publish"},
    RoleName.SCANNER: {"ticket:scan"},
}


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(132), nullable=False, unique=True)

    # Владелец компании определяется ТОЛЬКО через CompanyMembers.role == OWNER.
    # Поля owner_id здесь нет — единственный источник правды — CompanyMembers.
    members: Mapped[list["CompanyMembers"]] = relationship(
        "CompanyMembers",
        back_populates="company",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, slug={self.slug})>"

    def __str__(self) -> str:
        return self.slug


class CompanyMembers(Base, TimestampMixin):
    __tablename__ = "company_members"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_company_member"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[RoleName] = mapped_column(
        SAEnum(RoleName, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    company: Mapped["Company"] = relationship("Company", back_populates="members")

    def __repr__(self) -> str:
        return f"<CompanyMembers(company_id={self.company_id}, user_id={self.user_id}, role={self.role})>"
