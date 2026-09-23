from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import AuditLog, User
from app.utils.dates import end_datetime, start_datetime


def record_audit(
    db: Session,
    *,
    user: User,
    action: str,
    entity_type: str = "system",
    entity_id: int | None = None,
    details: dict | None = None,
) -> AuditLog:
    """Catat satu baris audit log (commit oleh pemanggil)."""
    log = AuditLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    return log


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def _filters(
        self,
        *,
        action: str | None,
        entity_type: str | None,
        user_id: int | None,
        start_date: date | None,
        end_date: date | None,
        q: str | None,
    ) -> list[Any]:
        filters = []
        if action:
            filters.append(AuditLog.action == action)
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)
        if q:
            filters.append(AuditLog.action.ilike(f"%{q.strip()}%"))
        if start_date:
            filters.append(AuditLog.created_at >= start_datetime(start_date))
        if end_date:
            filters.append(AuditLog.created_at <= end_datetime(end_date))
        return filters

    def list_logs(
        self,
        *,
        action: str | None = None,
        entity_type: str | None = None,
        user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        filters = self._filters(
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            q=q,
        )
        total = self.db.scalar(
            select(func.count(AuditLog.id)).where(*filters)
        ) or 0
        stmt = (
            select(AuditLog)
            .options(joinedload(AuditLog.user))
            .where(*filters)
            .order_by(AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).all())
        return items, total