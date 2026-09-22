from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, Product
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    def count(self) -> int:
        return self.db.scalar(select(func.count(Category.id))) or 0


class ProductRepository(BaseRepository[Product]):
    model = Product

    def count(self, filters: list[Any] | None = None) -> int:
        stmt = select(func.count(Product.id))
        if filters:
            stmt = stmt.where(*filters)
        return self.db.scalar(stmt) or 0

    def paginate(
        self,
        filters: list[Any] | None = None,
        *,
        page: int = 1,
        page_size: int = 20,
        order_by: Any = Product.id,
    ) -> list[Product]:
        stmt = select(Product).order_by(order_by)
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(stmt).all())