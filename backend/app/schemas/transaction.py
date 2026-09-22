from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models import PaymentMethod


class TransactionItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=999)
    note: str | None = Field(default=None, max_length=255)


class TransactionCreateRequest(BaseModel):
    items: list[TransactionItemRequest] = Field(min_length=1, max_length=50)
    payment_method: PaymentMethod
    paid_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    discount: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=2
    )


class TransactionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    price: Decimal
    quantity: int
    subtotal: Decimal
    note: str | None

    @field_serializer("price", "subtotal")
    def serialize_money(self, value: Decimal) -> float:
        return float(value)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    method: str
    amount: Decimal
    change_amount: Decimal

    @field_serializer("amount", "change_amount")
    def serialize_money(self, value: Decimal) -> float:
        return float(value)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    cashier_id: int
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    payment_method: str
    paid_amount: Decimal
    change_amount: Decimal
    status: str
    created_at: datetime
    items: list[TransactionItemOut]
    payment: PaymentOut | None = None

    @field_serializer("subtotal", "discount", "total", "paid_amount", "change_amount")
    def serialize_money(self, value: Decimal) -> float:
        return float(value)


class TransactionList(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int