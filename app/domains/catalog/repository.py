from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Category, Genre  # EventGenre — раскомментировать когда будет домен events


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: int) -> Category | None:
        return await self.db.get(Category, category_id)

    async def get_by_name(self, name: str) -> Category | None:
        query = select(Category).where(Category.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_categories(
        self,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Category], int]:
        query = select(Category)
        if search:
            query = query.where(Category.name.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar_one()

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def create(self, data: dict) -> Category:
        category = Category(**data)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: int, data: dict) -> Category | None:
        category = await self.get_by_id(category_id)
        if not category:
            return None
        for key, value in data.items():
            setattr(category, key, value)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: int) -> bool:
        category = await self.get_by_id(category_id)
        if not category:
            return False
        await self.db.delete(category)
        await self.db.flush()
        return True


class GenreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, genre_id: int) -> Genre | None:
        return await self.db.get(Genre, genre_id)

    async def get_by_name(self, name: str) -> Genre | None:
        query = select(Genre).where(Genre.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_genres(
        self,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Genre], int]:
        query = select(Genre)
        if search:
            query = query.where(Genre.name.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar_one()

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def create(self, data: dict) -> Genre:
        genre = Genre(**data)
        self.db.add(genre)
        await self.db.flush()
        await self.db.refresh(genre)
        return genre

    async def update(self, genre_id: int, data: dict) -> Genre | None:
        genre = await self.get_by_id(genre_id)
        if not genre:
            return None
        for key, value in data.items():
            setattr(genre, key, value)
        await self.db.flush()
        await self.db.refresh(genre)
        return genre

    async def delete(self, genre_id: int) -> bool:
        genre = await self.get_by_id(genre_id)
        if not genre:
            return False
        await self.db.delete(genre)
        await self.db.flush()
        return True



# TODO: раскомментировать когда будет домен events
# class EventGenreRepository:
#     def __init__(self, db: AsyncSession):
#         self.db = db
#
#     async def get_by_id(self, event_genre_id: int) -> EventGenre | None:
#         return await self.db.get(EventGenre, event_genre_id)
#
#     async def get_by_event_id(self, event_id: int) -> list[EventGenre]:
#         query = select(EventGenre).where(EventGenre.event_id == event_id)
#         result = await self.db.execute(query)
#         return list(result.scalars().all())
#
#     async def get_by_event_and_genre(
#         self, event_id: int, genre_id: int
#     ) -> EventGenre | None:
#         query = select(EventGenre).where(
#             EventGenre.event_id == event_id,
#             EventGenre.genre_id == genre_id,
#         )
#         result = await self.db.execute(query)
#         return result.scalar_one_or_none()
#
#     async def create(self, data: dict) -> EventGenre:
#         event_genre = EventGenre(**data)
#         self.db.add(event_genre)
#         await self.db.flush()
#         await self.db.refresh(event_genre)
#         return event_genre
#
#     async def delete(self, event_genre_id: int) -> bool:
#         event_genre = await self.get_by_id(event_genre_id)
#         if not event_genre:
#             return False
#         await self.db.delete(event_genre)
#         await self.db.flush()
#         return True
#
#     async def delete_by_event_id(self, event_id: int) -> None:
#         """Удалить все жанры мероприятия (bulk, без загрузки объектов)."""
#         query = delete(EventGenre).where(EventGenre.event_id == event_id)
#         await self.db.execute(query)
#         await self.db.flush()

