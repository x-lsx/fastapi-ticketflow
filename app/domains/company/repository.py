from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Company, CompanyMembers, RoleName


class CompanyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, company_id: int) -> Company | None:
        return await self.db.get(Company, company_id)

    async def get_by_slug(self, slug: str) -> Company | None:
        query = select(Company).where(Company.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name_and_user_id(self, name: str, user_id: int) -> Company | None:
        """Ищет компанию по имени среди компаний, где user является OWNER."""
        query = (
            select(Company)
            .join(CompanyMembers, CompanyMembers.company_id == Company.id)
            .where(
                Company.name == name,
                CompanyMembers.user_id == user_id,
                CompanyMembers.role == RoleName.OWNER,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_companies(
        self,
        search: str | None = None,
        member_user_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Company], int]:
        """
        Листинг компаний с необязательным фильтром по участнику.
        member_user_id — вернуть только компании, в которых этот user состоит
        (любая роль).
        """
        query = select(Company)

        if member_user_id is not None:
            query = query.join(
                CompanyMembers, CompanyMembers.company_id == Company.id
            ).where(CompanyMembers.user_id == member_user_id)

        if search:
            query = query.where(Company.name.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar_one()

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def create(self, data: dict) -> Company:
        company = Company(**data)
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def update(self, company_id: int, data: dict) -> Company | None:
        company = await self.get_by_id(company_id)
        if not company:
            return None
        for key, value in data.items():
            setattr(company, key, value)
        await self.db.flush()
        await self.db.refresh(company)
        return company


class CompanyMembersRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_members_by_company_id(self, company_id: int) -> list[CompanyMembers]:
        result = await self.db.execute(
            select(CompanyMembers).where(CompanyMembers.company_id == company_id)
        )
        return list(result.scalars().all())

    async def get_member(self, company_id: int, user_id: int) -> CompanyMembers | None:
        """Возвращает запись участника по компании и пользователю."""
        query = select(CompanyMembers).where(
            CompanyMembers.company_id == company_id,
            CompanyMembers.user_id == user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_owner(self, company_id: int) -> CompanyMembers | None:
        """Возвращает участника с ролью OWNER для данной компании."""
        query = select(CompanyMembers).where(
            CompanyMembers.company_id == company_id,
            CompanyMembers.role == RoleName.OWNER,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_member(self, data: dict) -> CompanyMembers:
        member = CompanyMembers(**data)
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def update_member_role(
        self, company_id: int, user_id: int, role: RoleName
    ) -> CompanyMembers | None:
        member = await self.get_member(company_id, user_id)
        if not member:
            return None
        member.role = role
        await self.db.flush()
        await self.db.refresh(member)
        return member