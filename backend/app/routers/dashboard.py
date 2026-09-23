from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import RoleEnum
from app.schemas.dashboard import (
    BestSellerList,
    DashboardSummary,
    SalesPoint,
)
from app.services.dashboard_service import DashboardService
from app.utils.dates import clamp_date_range

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _get_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    service: DashboardService = Depends(_get_service),
    _: object = Depends(require_roles(RoleEnum.OWNER)),
):
    start_date, end_date = clamp_date_range(start_date, end_date)
    return service.summary(start_date, end_date)


@router.get("/sales", response_model=list[SalesPoint])
def sales_series(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    group_by: str = Query(default="day", pattern="^(day|month)$"),
    service: DashboardService = Depends(_get_service),
    _: object = Depends(require_roles(RoleEnum.OWNER)),
):
    start_date, end_date = clamp_date_range(start_date, end_date)
    return service.sales_series(start_date, end_date, group_by)


@router.get("/best-sellers", response_model=BestSellerList)
def best_sellers(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=50),
    service: DashboardService = Depends(_get_service),
    _: object = Depends(require_roles(RoleEnum.OWNER)),
):
    start_date, end_date = clamp_date_range(start_date, end_date)
    return BestSellerList(items=service.best_sellers(start_date, end_date, limit))