import enum

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoleEnum(str, enum.Enum):
    OWNER = "OWNER"
    KASIR = "KASIR"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")

    @property
    def is_seed(self) -> bool:
        return self.name in {r.value for r in RoleEnum}