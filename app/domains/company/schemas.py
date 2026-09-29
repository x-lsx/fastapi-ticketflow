from pydantic import BaseModel, ConfigDict, Field

from app.domains.company.models import RoleName


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------


class CompanyCreate(BaseModel):
    name: str = Field(..., max_length=100, description="Название компании.")

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "MyCompany"}}
    )


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, max_length=100, description="Новое название компании.")


class CompanyResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# CompanyMembers
# ---------------------------------------------------------------------------


class CompanyMemberResponse(BaseModel):
    id: int
    company_id: int
    user_id: int
    role: RoleName

    model_config = ConfigDict(from_attributes=True)


class TransferOwnershipRequest(BaseModel):
    to_user_id: int = Field(..., description="ID пользователя, которому передаётся владение.")

    model_config = ConfigDict(
        json_schema_extra={"example": {"to_user_id": 42}}
    )
