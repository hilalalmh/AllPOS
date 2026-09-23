from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import RoleEnum, User
from app.services.audit_service import record_audit
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


def _report_params(
    start_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    payment_method: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    return {
        "start_date": start_date,
        "end_date": end_date,
        "payment_method": payment_method,
        "status": status,
    }


@router.get("/transactions.csv")
def transactions_csv(
    params: dict = Depends(_report_params),
    service: ReportService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    content = service.transactions_csv(**params)
    record_audit(
        service.db,
        user=current_user,
        action="report.csv",
        entity_type="report",
        details={"report": "transactions"},
    )
    service.db.flush()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/transactions.pdf")
def transactions_pdf(
    params: dict = Depends(_report_params),
    service: ReportService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    content = service.transactions_pdf(**params)
    record_audit(
        service.db,
        user=current_user,
        action="report.pdf",
        entity_type="report",
        details={"report": "transactions"},
    )
    service.db.flush()
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=transactions.pdf"},
    )