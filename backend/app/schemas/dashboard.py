from datetime import date

from pydantic import BaseModel, Field


class SalesPoint(BaseModel):
    period: str
    sales_total: float
    transaction_count: int


class BestSellerItem(BaseModel):
    product_name: str
    quantity: int
    revenue: float


class BestSellerList(BaseModel):
    items: list[BestSellerItem]


class DashboardSummary(BaseModel):
    start_date: date
    end_date: date
    sales_total: float
    transaction_count: int
    item_count: int
    active_products: int
    best_seller: BestSellerItem | None = None