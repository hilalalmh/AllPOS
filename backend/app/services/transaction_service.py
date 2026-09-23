from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Payment,
    PaymentMethod,
    Product,
    RoleEnum,
    Transaction,
    TransactionItem,
    TransactionStatus,
    User,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreateRequest
from app.utils.dates import end_datetime, start_datetime


class TransactionValidationError(Exception):
    pass


class TransactionNotFoundError(Exception):
    pass


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.transactions = TransactionRepository(db)
        self.products = ProductRepository(db)

    def create_transaction(
        self, cashier: User, payload: TransactionCreateRequest
    ) -> Transaction:
        if payload.local_ref is not None:
            existing = self.db.scalar(
                select(Transaction).where(Transaction.local_ref == payload.local_ref)
            )
            if existing is not None:
                return existing
        items_data = []
        subtotal = Decimal("0")

        for item in payload.items:
            product = self.products.get(item.product_id)
            if product is None or not product.is_active:
                raise TransactionValidationError(
                    f"Produk id={item.product_id} tidak ditemukan atau tidak aktif."
                )
            price = product.price
            line_subtotal = price * item.quantity
            subtotal += line_subtotal
            items_data.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "price": price,
                    "quantity": item.quantity,
                    "subtotal": line_subtotal,
                    "note": item.note,
                }
            )

        discount = payload.discount
        if discount > subtotal:
            raise TransactionValidationError(
                "Discount tidak boleh melebihi subtotal."
            )
        total = subtotal - discount

        paid = payload.paid_amount
        if paid < total:
            raise TransactionValidationError("Pembayaran tidak mencukupi.")
        change = paid - total

        for attempt in range(5):
            try:
                return self._persist(
                    cashier,
                    items_data,
                    subtotal,
                    discount,
                    total,
                    payload.payment_method,
                    paid,
                    change,
                    local_ref=payload.local_ref,
                )
            except IntegrityError:
                self.db.rollback()
                if payload.local_ref is not None:
                    existing = self.db.scalar(
                        select(Transaction).where(
                            Transaction.local_ref == payload.local_ref
                        )
                    )
                    if existing is not None:
                        return existing
                if attempt == 4:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Gagal membuat nomor invoice unik. Coba lagi.",
                    )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal membuat transaksi.",
        )

    def _persist(
        self,
        cashier: User,
        items_data: list[dict],
        subtotal: Decimal,
        discount: Decimal,
        total: Decimal,
        payment_method: PaymentMethod,
        paid: Decimal,
        change: Decimal,
        local_ref: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            invoice_number=self._next_invoice_number(),
            local_ref=local_ref,
            cashier_id=cashier.id,
            subtotal=subtotal,
            discount=discount,
            total=total,
            payment_method=payment_method.value,
            paid_amount=paid,
            change_amount=change,
            status=TransactionStatus.PAID.value,
        )
        self.db.add(transaction)
        self.db.flush()

        transaction.items = [
            TransactionItem(transaction_id=transaction.id, **data)
            for data in items_data
        ]
        self.db.add(
            Payment(
                transaction_id=transaction.id,
                method=payment_method.value,
                amount=paid,
                change_amount=change,
            )
        )
        self._log(
            cashier,
            action="transaction.create",
            entity_id=transaction.id,
            details={
                "invoice_number": transaction.invoice_number,
                "total": str(total),
            },
        )
        self.db.flush()
        return transaction

    def _next_invoice_number(self) -> str:
        day = datetime.now().strftime("%Y%m%d")
        prefix = f"POS-{day}-"
        count = (
            self.db.scalar(
                select(func.count(Transaction.id)).where(
                    Transaction.invoice_number.like(f"{prefix}%")
                )
            )
            or 0
        )
        return f"{prefix}{count + 1:04d}"

    def get_transaction(self, user: User, transaction_id: int) -> Transaction:
        transaction = self.transactions.get_with_detail(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError("Transaksi tidak ditemukan.")
        if user.role.name != RoleEnum.OWNER.value and transaction.cashier_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak berhak mengakses transaksi ini.",
            )
        return transaction

    def cancel_transaction(self, user: User, transaction_id: int) -> Transaction:
        transaction = self.get_transaction(user, transaction_id)
        if transaction.status == TransactionStatus.CANCELLED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaksi sudah dibatalkan.",
            )
        transaction.status = TransactionStatus.CANCELLED.value
        self._log(
            user,
            action="transaction.cancel",
            entity_id=transaction.id,
            details={"invoice_number": transaction.invoice_number},
        )
        self.db.flush()
        return transaction

    def list_transactions(
        self,
        user: User,
        *,
        q: str | None,
        cashier_id: int | None,
        payment_method: str | None,
        status_filter: str | None,
        start_date: str | None,
        end_date: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Transaction], int]:
        filters = []
        if user.role.name != RoleEnum.OWNER.value:
            filters.append(Transaction.cashier_id == user.id)
        else:
            if cashier_id is not None:
                filters.append(Transaction.cashier_id == cashier_id)

        if q:
            filters.append(Transaction.invoice_number.ilike(f"%{q.strip()}%"))
        if payment_method:
            filters.append(Transaction.payment_method == payment_method.upper())
        if status_filter:
            filters.append(Transaction.status == status_filter.upper())

        if start_date:
            parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
            filters.append(Transaction.created_at >= start_datetime(parsed))
        if end_date:
            parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
            filters.append(Transaction.created_at <= end_datetime(parsed))

        total = self.transactions.count_filtered(filters)
        items = self.transactions.paginate_filtered(
            filters, page=page, page_size=page_size
        )
        return items, total

    def _log(
        self,
        user: User,
        *,
        action: str,
        entity_id: int | None = None,
        details: dict | None = None,
    ) -> None:
        self.db.add(
            AuditLog(
                user_id=user.id,
                action=action,
                entity_type="transaction",
                entity_id=entity_id,
                details=details,
            )
        )