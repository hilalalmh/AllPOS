from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    model = Transaction

    _LOAD = (
        selectinload(Transaction.items),
        selectinload(Transaction.payment),
    )

    def get_with_detail(self, id: int) -> Transaction | None:
        stmt = (
            select(Transaction)
            .options(*self._LOAD)
            .where(Transaction.id == id)
        )
        return self.db.scalar(stmt)

    def count_filtered(self, filters: list[Any]) -> int:
        stmt = select(func.count(Transaction.id)).where(*filters)
        return self.db.scalar(stmt) or 0

    def paginate_filtered(
        self,
        filters: list[Any],
        *,
        page: int,
        page_size: int,
    ) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .options(*self._LOAD)
            .where(*filters)
            .order_by(Transaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all())


def today_str() -> str:
    return datetime.now().strftime("%Y%m%d")