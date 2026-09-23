from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionList,
    TransactionOut,
)
from app.services.transaction_service import (
    TransactionNotFoundError,
    TransactionService,
    TransactionValidationError,
)
from app.utils.dates import clamp_date_range

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _get_service(db: Session = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, TransactionValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    if isinstance(exc, TransactionNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    raise exc


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    try:
        return service.create_transaction(current_user, payload)
    except Exception as exc:
        _handle_error(exc)


@router.get("", response_model=TransactionList)
def list_transactions(
    q: str | None = Query(default=None, max_length=30),
    cashier_id: int | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    start_date, end_date = clamp_date_range(start_date, end_date)
    items, total = service.list_transactions(
        current_user,
        q=q,
        cashier_id=cashier_id,
        payment_method=payment_method,
        status_filter=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return TransactionList(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    try:
        return service.get_transaction(current_user, transaction_id)
    except Exception as exc:
        _handle_error(exc)


@router.post("/{transaction_id}/cancel", response_model=TransactionOut)
def cancel_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(_get_service),
):
    try:
        return service.cancel_transaction(current_user, transaction_id)
    except Exception as exc:
        _handle_error(exc)