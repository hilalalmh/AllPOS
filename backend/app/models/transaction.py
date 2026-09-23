import enum

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    QRIS = "QRIS"
    TRANSFER = "TRANSFER"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    local_ref: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )
    cashier_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    payment_method: Mapped[str] = mapped_column(String(20))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    change_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    status: Mapped[str] = mapped_column(
        String(20), default=TransactionStatus.PENDING.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    cashier: Mapped["User"] = relationship()  # type: ignore[name-defined]
    items: Mapped[list["TransactionItem"]] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="TransactionItem.id",
    )
    payment: Mapped["Payment | None"] = relationship(
        back_populates="transaction", cascade="all, delete-orphan", uselist=False
    )


class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    product_name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    transaction: Mapped["Transaction"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()  # type: ignore[name-defined]


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, index=True
    )
    method: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    change_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transaction: Mapped["Transaction"] = relationship(back_populates="payment")