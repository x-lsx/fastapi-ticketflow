import logging
import math

from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse

from .exceptions import (
    AlreadyOwner,
    CompanyAlreadyExists,
    CompanyNotFound,
    CompanyOwnerNotFound,
    TransferTargetNotMember,
)
from .models import RoleName
from .repository import CompanyMembersRepository, CompanyRepository
from .schemas import (
    CompanyCreate,
    CompanyMemberResponse,
    CompanyResponse,
    CompanyUpdate,
)

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = CompanyRepository(db)
        self.members_repo = CompanyMembersRepository(db)
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_or_404(self, company_id: int) -> object:
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise CompanyNotFound(f"Company {company_id} not found")
        return company

    async def _generate_slug(self, name: str) -> str:
        base_slug = slugify(name)
        slug = base_slug
        index = 1
        while await self.repo.get_by_slug(slug):
            slug = f"{base_slug}-{index}"
            index += 1
        return slug

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_company(self, company_id: int) -> CompanyResponse:
        company = await self._get_or_404(company_id)
        return CompanyResponse.model_validate(company)

    async def list_companies(
        self,
        search: str | None = None,
        member_user_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[CompanyResponse]:
        offset = (page - 1) * size
        companies, total = await self.repo.list_companies(
            search=search,
            member_user_id=member_user_id,
            limit=size,
            offset=offset,
        )
        return PaginatedResponse(
            items=[CompanyResponse.model_validate(c) for c in companies],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 1,
        )

    async def create_company(
        self, data: CompanyCreate, user_id: int
    ) -> CompanyResponse:
        """
        Создаёт Company и сразу CompanyMembers(role=OWNER) в одной транзакции.
        Это единственный способ создать компанию — без привязанного OWNER
        компания не создаётся.
        """
        existing = await self.repo.get_by_name_and_user_id(
            name=data.name, user_id=user_id
        )
        if existing:
            raise CompanyAlreadyExists(
                f"Company with name '{data.name}' already exists for this user"
            )

        slug = await self._generate_slug(data.name)

        # Flush company первым, чтобы получить id до создания члена
        company = await self.repo.create({"name": data.name, "slug": slug})

        # Сразу создаём запись владельца в той же транзакции
        await self.members_repo.create_member(
            {
                "company_id": company.id,
                "user_id": user_id,
                "role": RoleName.OWNER,
            }
        )

        await self.db.commit()
        await self.db.refresh(company)
        return CompanyResponse.model_validate(company)

    async def update_company(
        self, company_id: int, data: CompanyUpdate
    ) -> CompanyResponse:
        await self._get_or_404(company_id)
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload:
            payload["slug"] = await self._generate_slug(payload["name"])
        updated = await self.repo.update(company_id, payload)
        await self.db.commit()
        return CompanyResponse.model_validate(updated)

    async def transfer_ownership(
        self, company_id: int, from_user_id: int, to_user_id: int
    ) -> CompanyMemberResponse:
        """
        Передаёт владение компанией другому участнику.
        - to_user_id обязан уже быть членом компании.
        - Текущий OWNER понижается до MANAGER.
        - Новый OWNER — to_user_id.
        - В компании всегда ровно один OWNER.
        """
        await self._get_or_404(company_id)

        if from_user_id == to_user_id:
            raise AlreadyOwner("User is already the owner of this company")

        # Проверяем, что текущий owner действительно OWNER
        current_owner = await self.members_repo.get_owner(company_id)
        if not current_owner or current_owner.user_id != from_user_id:
            raise CompanyOwnerNotFound(
                f"User {from_user_id} is not the owner of company {company_id}"
            )

        # Проверяем, что to_user является членом компании
        target_member = await self.members_repo.get_member(company_id, to_user_id)
        if not target_member:
            raise TransferTargetNotMember(
                f"User {to_user_id} is not a member of company {company_id}"
            )

        if target_member.role == RoleName.OWNER:
            raise AlreadyOwner(f"User {to_user_id} is already the owner")

        # Меняем роли атомарно в рамках одной транзакции
        await self.members_repo.update_member_role(
            company_id, from_user_id, RoleName.MANAGER
        )
        new_owner = await self.members_repo.update_member_role(
            company_id, to_user_id, RoleName.OWNER
        )

        await self.db.commit()
        return CompanyMemberResponse.model_validate(new_owner)
