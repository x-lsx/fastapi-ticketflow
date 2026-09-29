from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=100, description="Название категории.")

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Концерт"}}
    )


class CategoryResponse(BaseModel):
    id: int = Field(..., description="ID категории.")
    name: str = Field(..., description="Название категории.")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Genre
# ---------------------------------------------------------------------------


class GenreCreate(BaseModel):
    name: str = Field(..., max_length=100, description="Название жанра.")

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Рок"}}
    )


class GenreResponse(BaseModel):
    id: int = Field(..., description="ID жанра.")
    name: str = Field(..., description="Название жанра.")

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# EventGenre
# ---------------------------------------------------------------------------


# TODO: раскомментировать когда будет домен events
# class EventGenreCreate(BaseModel):
#     event_id: int = Field(..., description="ID мероприятия.")
#     genre_id: int = Field(..., description="ID жанра.")
#
#     model_config = ConfigDict(
#         json_schema_extra={"example": {"event_id": 1, "genre_id": 3}}
#     )
#
#
# class EventGenreResponse(BaseModel):
#     id: int = Field(..., description="ID связи.")
#     event_id: int = Field(..., description="ID мероприятия.")
#     genre_id: int = Field(..., description="ID жанра.")
#
#     model_config = ConfigDict(from_attributes=True)
