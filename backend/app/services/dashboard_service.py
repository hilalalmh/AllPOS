from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Product, Transaction, TransactionItem, TransactionStatus
from app.schemas.dashboard import (
    BestSellerItem,
    DashboardSummary,
    SalesPoint,
)
from app.utils.dates import business_day_bounds


def resolve_range(
    start_date: date | None, end_date: date | None
) -> tuple[datetime, datetime]:
    return business_day_bounds(start_date, end_date)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _active_filter(start: datetime, end: datetime):
        return and_(
            Transaction.status != TransactionStatus.CANCELLED.value,
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        )

    def summary(self, start_date: date | None, end_date: date | None) -> DashboardSummary:
        start, end = resolve_range(start_date, end_date)
        filt = self._active_filter(start, end)

        sales_total = self.db.execute(
            select(func.coalesce(func.sum(Transaction.total), 0)).where(filt)
        ).scalar_one()
        transaction_count = self.db.execute(
            select(func.count(Transaction.id)).where(filt)
        ).scalar_one()
        item_count = self.db.execute(
            select(func.coalesce(func.sum(TransactionItem.quantity), 0))
            .select_from(Transaction)
            .join(TransactionItem)
            .where(filt)
        ).scalar_one()
        active_products = self.db.execute(
            select(func.count(Product.id)).where(Product.is_active.is_(True))
        ).scalar_one()

        best = self.best_sellers(start_date, end_date, limit=1)
        return DashboardSummary(
            start_date=start.date(),
            end_date=end.date(),
            sales_total=float(sales_total),
            transaction_count=int(transaction_count),
            item_count=int(item_count),
            active_products=int(active_products),
            best_seller=best[0] if best else None,
        )

    def sales_series(
        self,
        start_date: date | None,
        end_date: date | None,
        group_by: str = "day",
    ) -> list[SalesPoint]:
        start, end = resolve_range(start_date, end_date)
        fmt = "YYYY-MM" if group_by == "month" else "YYYY-MM-DD"
        wib_expr = Transaction.created_at.op("AT TIME ZONE")("Asia/Jakarta")
        period_expr = func.to_char(wib_expr, fmt).label("period")
        stmt = (
            select(
                period_expr,
                func.coalesce(func.sum(Transaction.total), 0).label("sales_total"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .where(self._active_filter(start, end))
            .group_by(period_expr)
            .order_by(period_expr)
        )
        rows = self.db.execute(stmt).all()
        return [
            SalesPoint(
                period=row.period,
                sales_total=float(row.sales_total),
                transaction_count=int(row.transaction_count),
            )
            for row in rows
        ]

    def best_sellers(
        self,
        start_date: date | None,
        end_date: date | None,
        limit: int = 5,
    ) -> list[BestSellerItem]:
        start, end = resolve_range(start_date, end_date)
        stmt = (
            select(
                TransactionItem.product_name,
                func.sum(TransactionItem.quantity).label("quantity"),
                func.sum(TransactionItem.subtotal).label("revenue"),
            )
            .join(Transaction, TransactionItem.transaction_id == Transaction.id)
            .where(self._active_filter(start, end))
            .group_by(TransactionItem.product_name)
            .order_by(
                func.sum(TransactionItem.quantity).desc(),
                func.sum(TransactionItem.subtotal).desc(),
            )
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        return [
            BestSellerItem(
                product_name=row.product_name,
                quantity=int(row.quantity),
                revenue=float(row.revenue),
            )
            for row in rows
        ]