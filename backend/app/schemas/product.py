from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ProductBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    sku: str | None = Field(default=None, max_length=50)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    image_url: str | None = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    sku: str | None = Field(default=None, max_length=50)
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    image_url: str | None = None
    is_active: bool | None = None


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> float:
        return float(value)


class ProductList(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int