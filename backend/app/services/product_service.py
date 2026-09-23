from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Category, Product
from app.repositories.product_repository import (
    CategoryRepository,
    ProductRepository,
)
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.product import ProductCreate, ProductUpdate


class CategoryNotFoundError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class DuplicateSkuError(Exception):
    pass


class DuplicateCategoryNameError(Exception):
    pass


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.categories = CategoryRepository(db)
        self.products = ProductRepository(db)

    # Kolom NOT NULL tidak boleh di-update ke null (mis. payload eksplisit
    # {"name": null}) — pydantic mengizinkan None karena optional, jadi dicegah
    # di sini dengan 422 agar tidak memicu 500 IntegrityError di flush.
    _NON_NULLABLE_PRODUCT_FIELDS = frozenset({"category_id", "name", "price", "is_active"})
    _NON_NULLABLE_CATEGORY_FIELDS = frozenset({"name", "is_active"})

    # ---- Categories ----

    def list_categories(self, active_only: bool = True) -> list[Category]:
        filters = []
        if active_only:
            filters.append(Category.is_active.is_(True))
        stmt = select(Category).order_by(Category.name)
        if filters:
            stmt = stmt.where(*filters)
        return list(self.db.scalars(stmt).all())

    def get_category(self, category_id: int) -> Category | None:
        return self.categories.get(category_id)

    def create_category(self, payload: CategoryCreate) -> Category:
        existing = self.categories.get_by(name=payload.name)
        if existing is not None:
            raise DuplicateCategoryNameError("Nama kategori sudah digunakan.")
        category = Category(name=payload.name, is_active=payload.is_active)
        self.categories.add(category, flush=True)
        return category

    def update_category(
        self, category_id: int, payload: CategoryUpdate
    ) -> Category:
        category = self.categories.get(category_id)
        if category is None:
            raise CategoryNotFoundError("Kategori tidak ditemukan.")
        data = payload.model_dump(exclude_unset=True)
        for field in self._NON_NULLABLE_CATEGORY_FIELDS & data.keys():
            if data[field] is None:
                raise HTTPException(
                    status_code=422, detail=f"{field} tidak boleh bernilai null."
                )
        if "name" in data and data["name"] != category.name:
            existing = self.categories.get_by(name=data["name"])
            if existing is not None:
                raise DuplicateCategoryNameError("Nama kategori sudah digunakan.")
        for field, value in data.items():
            setattr(category, field, value)
        self.db.flush()
        return category

    def delete_category(self, category_id: int) -> None:
        category = self.categories.get(category_id)
        if category is None:
            raise CategoryNotFoundError("Kategori tidak ditemukan.")
        has_products = self.db.scalar(
            select(Product.id).where(Product.category_id == category_id).limit(1)
        )
        if has_products is not None:
            category.is_active = False
        else:
            self.db.delete(category)
        self.db.flush()

    # ---- Products ----

    def list_products(
        self,
        *,
        q: str | None = None,
        category_id: int | None = None,
        include_inactive: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        filters = []
        if q:
            pattern = f"%{q.strip()}%"
            filters.append(
                or_(
                    Product.name.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            )
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        if not include_inactive:
            filters.append(Product.is_active.is_(True))

        total = self.products.count(filters)
        items = self.products.paginate(
            filters, page=page, page_size=page_size, order_by=Product.name
        )
        return items, total

    def get_product(self, product_id: int) -> Product | None:
        return self.products.get(product_id)

    def create_product(self, payload: ProductCreate) -> Product:
        self._ensure_category_exists(payload.category_id)
        if payload.sku and self.products.get_by(sku=payload.sku):
            raise DuplicateSkuError("SKU sudah digunakan.")
        product = Product(**payload.model_dump())
        self.products.add(product, flush=True)
        return product

    def update_product(
        self, product_id: int, payload: ProductUpdate
    ) -> Product:
        product = self.products.get(product_id)
        if product is None:
            raise ProductNotFoundError("Produk tidak ditemukan.")
        data = payload.model_dump(exclude_unset=True)
        for field in self._NON_NULLABLE_PRODUCT_FIELDS & data.keys():
            if data[field] is None:
                raise HTTPException(
                    status_code=422, detail=f"{field} tidak boleh bernilai null."
                )

        if "category_id" in data and data["category_id"] is not None:
            self._ensure_category_exists(data["category_id"])
        if "sku" in data and data["sku"]:
            existing = self.products.get_by(sku=data["sku"])
            if existing is not None and existing.id != product_id:
                raise DuplicateSkuError("SKU sudah digunakan.")

        for field, value in data.items():
            setattr(product, field, value)
        self.db.flush()
        return product

    def delete_product(self, product_id: int) -> None:
        product = self.products.get(product_id)
        if product is None:
            raise ProductNotFoundError("Produk tidak ditemukan.")
        product.is_active = False
        self.db.flush()

    def _ensure_category_exists(self, category_id: int) -> None:
        category = self.categories.get(category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kategori tidak ditemukan.",
            )
        if not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kategori tidak aktif.",
            )