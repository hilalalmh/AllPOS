from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import RoleEnum
from app.schemas.audit import AuditLogList, AuditLogOut
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _get_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)


@router.get("", response_model=AuditLogList)
def list_audit_logs(
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    start_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    q: str | None = Query(default=None, max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: AuditService = Depends(_get_service),
    _: object = Depends(require_roles(RoleEnum.OWNER)),
):
    items, total = service.list_logs(
        action=action,
        entity_type=entity_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        q=q,
        page=page,
        page_size=page_size,
    )
    return AuditLogList(
        items=[AuditLogOut.from_orm_with_user(log) for log in items],
        total=total,
        page=page,
        page_size=page_size,
    )