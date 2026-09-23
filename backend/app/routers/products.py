from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.storage import delete_image, save_image
from app.models import RoleEnum, User
from app.schemas.product import (
    ProductCreate,
    ProductList,
    ProductOut,
    ProductUpdate,
)
from app.services.audit_service import record_audit
from app.services.product_service import (
    DuplicateSkuError,
    ProductNotFoundError,
    ProductService,
)

router = APIRouter(prefix="/products", tags=["products"])


def _get_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, ProductNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DuplicateSkuError):
        raise HTTPException(status_code=409, detail=str(exc))
    raise exc


def _raise(exc: Exception) -> None:
    _handle_service_error(exc)
    raise exc


@router.get("", response_model=ProductList)
def list_products(
    q: str | None = Query(default=None, max_length=100),
    category_id: int | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ProductService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
):
    if include_inactive and current_user.role.name != RoleEnum.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya OWNER yang boleh melihat produk nonaktif.",
        )
    items, total = service.list_products(
        q=q,
        category_id=category_id,
        include_inactive=include_inactive,
        page=page,
        page_size=page_size,
    )
    return ProductList(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    service: ProductService = Depends(_get_service),
    _: object = Depends(get_current_user),
):
    product = service.get_product(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan."
        )
    return product


@router.post(
    "",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    category_id: int = Form(...),
    name: str = Form(..., min_length=1, max_length=100),
    description: str | None = Form(default=None),
    sku: str | None = Form(default=None, max_length=50),
    price: float = Form(..., gt=0),
    is_active: bool = Form(default=True),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    # Route sinkron agar file I/O tidak memblokir event loop; penyimpanan
    # gambar + konstruksi payload berada dalam try sehingga gambar yang
    # tersimpan tidak jadi yatim bila validasi/insert gagal.
    service = ProductService(db)
    image_url = None
    try:
        if image is not None:
            image_url = save_image(image)
        payload = ProductCreate(
            category_id=category_id,
            name=name,
            description=description,
            sku=sku,
            price=Decimal(str(price)),
            image_url=image_url,
            is_active=is_active,
        )
        product = service.create_product(payload)
    except Exception as exc:
        if image_url:
            delete_image(image_url)
        _raise(exc)
    record_audit(
        db,
        user=current_user,
        action="product.create",
        entity_type="product",
        entity_id=product.id,
        details={"name": product.name, "sku": product.sku},
    )
    db.flush()
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    service: ProductService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    try:
        product = service.update_product(product_id, payload)
    except Exception as exc:
        _raise(exc)
    record_audit(
        service.db,
        user=current_user,
        action="product.update",
        entity_type="product",
        entity_id=product.id,
        details={"name": product.name, "sku": product.sku},
    )
    service.db.flush()
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: int,
    service: ProductService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    product = service.get_product(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produk tidak ditemukan."
        )
    try:
        service.delete_product(product_id)
    except Exception as exc:
        _raise(exc)
    record_audit(
        service.db,
        user=current_user,
        action="product.delete",
        entity_type="product",
        entity_id=product_id,
        details={"name": product.name, "sku": product.sku},
    )
    service.db.flush()