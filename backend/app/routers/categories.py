from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import RoleEnum, User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.audit_service import record_audit
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
)
def create_category(
    payload: CategoryCreate,
    service: ProductService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    try:
        category = service.create_category(payload)
    except Exception as exc:
        _handle_service_error(exc)
    record_audit(
        service.db,
        user=current_user,
        action="category.create",
        entity_type="category",
        entity_id=category.id,
        details={"name": category.name},
    )
    service.db.flush()
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryOut,
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    service: ProductService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    try:
        category = service.update_category(category_id, payload)
    except Exception as exc:
        _handle_service_error(exc)
    record_audit(
        service.db,
        user=current_user,
        action="category.update",
        entity_type="category",
        entity_id=category.id,
        details={"name": category.name},
    )
    service.db.flush()
    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: int,
    service: ProductService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    category = service.get_category(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan.")
    try:
        service.delete_category(category_id)
    except Exception as exc:
        _handle_service_error(exc)
    record_audit(
        service.db,
        user=current_user,
        action="category.delete",
        entity_type="category",
        entity_id=category_id,
        details={"name": category.name},
    )
    service.db.flush()