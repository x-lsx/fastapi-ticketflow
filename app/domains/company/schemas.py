from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str = Field(..., description="Company name.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "myCompany",
            }
        }
    )
class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Company name.")


class CompanyResponse(BaseModel):
    id: int = Field(..., description="Company ID.")
    name: str = Field(..., description="Company name.")
    slug: str = Field(..., description="Company slug.")

    model_config = ConfigDict(from_attributes=True)
