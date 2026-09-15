from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int  # Всего записей в базе по фильтру
    page: int  # Текущая страница
    size: int  # Размер страницы
    pages: int  # Всего страниц
