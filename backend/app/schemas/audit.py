from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details: dict[str, Any] | None
    created_at: datetime
    username: str | None = None

    @classmethod
    def from_orm_with_user(cls, log) -> "AuditLogOut":
        return cls(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details,
            created_at=log.created_at,
            username=log.user.username if log.user else None,
        )


class AuditLogList(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int