import logging
import math
from typing import Optional

from app.domains.user.models import User
from fastapi import HTTPException, status
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import CompanyRepository
from .schemas import CompanyCreate, CompanyResponse


class CompanyService:
    def __init__(self, db: AsyncSession):
        self.repos = CompanyRepository(db)
        self.logger = logging.getLogger(__name__)

    async def _generate_slug(self, name: str) -> str:
        base_slug = slugify(name)
        slug = base_slug
        index = 1
        while await self.repos.get_by_slug(slug):
            slug = f"{base_slug}-{index}"
            index += 1
        return slug

    async def get_company_by_id(self, company_id: int) -> CompanyResponse:
        company = await self.repos.get_by_id(company_id=company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )
        return CompanyResponse.model_validate(company)

    async def get_company_by_name(
        self,
        search: str | None = None,
        page: int = 1,
        size: int = 10,
        owner_id: int | None = None,
    ) -> dict:

        offset = (page - 1) * size

        companies, total_count = await self.repos.get_by_name(
            search=search, limit=size, offset=offset, owner_id=owner_id
        )
        return {
            "items": [CompanyResponse.model_validate(c) for c in companies],
            "total": total_count,
            "page": page,
            "size": size,
            "pages": math.ceil(total_count / size) if total_count > 0 else 1,
        }

    async def create_company(
        self, company_data: CompanyCreate, current_user: User
    ) -> CompanyResponse:

        existting_company = await self.repos.get_by_name_and_owner_id(
            name=company_data.name, owner_id=current_user.id
        )
        if existting_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company with this name already exists",
            )
        slug = await self._generate_slug(company_data.name)
        new_data = company_data.model_dump()
        new_data["slug"] = slug
        new_data["owner_id"] = current_user.id
        company = await self.repos.create(company_data=new_data)
        await self.repos.db.commit()
        return CompanyResponse.model_validate(company)
