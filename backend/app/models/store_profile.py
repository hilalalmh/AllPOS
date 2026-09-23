from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StoreProfile(Base):
    __tablename__ = "store_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_name: Mapped[str] = mapped_column(
        String(100), default="SISTEM POS", server_default="SISTEM POS"
    )
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    footer: Mapped[str] = mapped_column(
        String(120),
        default="TERIMA KASIH ~ SILAHKAN DATANG KEMBALI",
        server_default="TERIMA KASIH ~ SILAHKAN DATANG KEMBALI",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
