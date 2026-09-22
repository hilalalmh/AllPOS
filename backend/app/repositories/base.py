from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> ModelT | None:
        return self.db.get(self.model, id)

    def get_by(self, **filters) -> ModelT | None:
        stmt = select(self.model).filter_by(**filters).limit(1)
        return self.db.scalar(stmt)

    def all(self) -> list[ModelT]:
        stmt = select(self.model)
        return list(self.db.scalars(stmt).all())

    def add(self, obj: ModelT, flush: bool = False) -> ModelT:
        self.db.add(obj)
        if flush:
            self.db.flush()
        return obj