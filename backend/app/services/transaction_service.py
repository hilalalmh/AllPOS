from datetime import date, datetime, timedelta, timezone
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
from app.utils.dates import BUSINESS_TZ, end_datetime, start_datetime

# Kolom Numeric(12,2) → maksimal 9,999,999,999.99
_MAX_MONEY = Decimal("9999999999.99")
# Toleransi jeda antar-perangkat saat kirim created_at_local (mis. sinkronisasi offline)
_MAX_FUTURE_SKEW = timedelta(minutes=5)


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

        if subtotal > _MAX_MONEY or total > _MAX_MONEY:
            raise TransactionValidationError(
                "Nilai transaksi melebihi batas maksimum."
            )

        paid = payload.paid_amount
        if paid < total:
            raise TransactionValidationError("Pembayaran tidak mencukupi.")
        if paid > _MAX_MONEY:
            raise TransactionValidationError(
                "Nilai pembayaran melebihi batas maksimum."
            )
        change = paid - total

        if payload.local_ref is not None:
            existing = self.db.scalar(
                select(Transaction).where(
                    Transaction.local_ref == payload.local_ref,
                    Transaction.cashier_id == cashier.id,
                )
            )
            if existing is not None:
                self._assert_replay_matches(existing, subtotal, discount, total, paid)
                return existing

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
                    created_at_local=payload.created_at_local,
                )
            except IntegrityError:
                self.db.rollback()
                if payload.local_ref is not None:
                    existing = self.db.scalar(
                        select(Transaction).where(
                            Transaction.local_ref == payload.local_ref,
                            Transaction.cashier_id == cashier.id,
                        )
                    )
                    if existing is not None:
                        self._assert_replay_matches(
                            existing, subtotal, discount, total, paid
                        )
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

    @staticmethod
    def _assert_replay_matches(
        existing: Transaction,
        subtotal: Decimal,
        discount: Decimal,
        total: Decimal,
        paid: Decimal,
    ) -> None:
        """Replay local_ref harus cocok dengan transaksi asli, jika tidak → 409."""
        if (
            (existing.subtotal or Decimal("0")) != subtotal
            or (existing.discount or Decimal("0")) != discount
            or (existing.total or Decimal("0")) != total
            or (existing.paid_amount or Decimal("0")) != paid
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="local_ref sudah dipakai untuk transaksi dengan isi berbeda.",
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
        created_at_local: datetime | None = None,
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
        if created_at_local is not None:
            local_dt = created_at_local
            if local_dt.tzinfo is None:
                local_dt = local_dt.replace(tzinfo=BUSINESS_TZ)
            now = datetime.now(timezone.utc)
            if local_dt - now > _MAX_FUTURE_SKEW:
                raise TransactionValidationError(
                    "created_at_local tidak boleh berada jauh di masa depan."
                )
            transaction.created_at = local_dt.astimezone(timezone.utc)
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
        day = datetime.now(BUSINESS_TZ).strftime("%Y%m%d")
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
        start_date: "date | None",
        end_date: "date | None",
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
            filters.append(Transaction.created_at >= start_datetime(start_date))
        if end_date:
            filters.append(Transaction.created_at <= end_datetime(end_date))

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