from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Company


class CompanyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, company_id: int) -> Company | None:
        return await self.db.get(Company, company_id)

    async def get_by_name(
        self,
        owner_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Company], int]:

        query = select(Company)
        if owner_id:
            query = query.where(Company.owner_id == owner_id)
        if search:
            query = query.where(Company.name.ilike(f"%{search}%"))
            
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar_one()

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        companies = list(result.scalars().all())
        
        return companies, total_count

    async def get_by_slug(self, slug: str) -> Company | None:
        query = select(Company).where(Company.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name_and_owner_id(
        self, name: str, owner_id: int
    ) -> Company | None:
        query = select(Company).where(
            Company.name == name, Company.owner_id == owner_id
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create(self, company_data: dict):
        company = Company(**company_data)
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def update(self, company_id: int, update_data: dict) -> Company | None:
        company = await self.get_by_id(company_id)
        if not company:
            return None
        for key, value in update_data.items():
            setattr(company, key, value)
        await self.db.flush()
        await self.db.refresh(company)
        return company
