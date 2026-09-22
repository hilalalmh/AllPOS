from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import RoleEnum
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.product_service import (
    CategoryNotFoundError,
    DuplicateCategoryNameError,
    ProductService,
)

router = APIRouter(prefix="/categories", tags=["categories"])


def _get_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, CategoryNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DuplicateCategoryNameError):
        raise HTTPException(status_code=409, detail=str(exc))
    raise exc


@router.get("", response_model=list[CategoryOut])
def list_categories(
    service: ProductService = Depends(_get_service),
    _: object = Depends(get_current_user),
):
    return service.list_categories(active_only=True)


@router.post(
    "",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleEnum.OWNER))],
)
def create_category(
    payload: CategoryCreate,
    service: ProductService = Depends(_get_service),
):
    try:
        return service.create_category(payload)
    except Exception as exc:
        _handle_service_error(exc)


@router.put(
    "/{category_id}",
    response_model=CategoryOut,
    dependencies=[Depends(require_roles(RoleEnum.OWNER))],
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    service: ProductService = Depends(_get_service),
):
    try:
        return service.update_category(category_id, payload)
    except Exception as exc:
        _handle_service_error(exc)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RoleEnum.OWNER))],
)
def delete_category(
    category_id: int,
    service: ProductService = Depends(_get_service),
):
    try:
        service.delete_category(category_id)
    except Exception as exc:
        _handle_service_error(exc)