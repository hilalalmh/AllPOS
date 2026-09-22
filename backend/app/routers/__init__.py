from fastapi import APIRouter

from app.routers import (
    auth,
    categories,
    dashboard,
    health,
    products,
    transactions,
)

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router)
router.include_router(categories.router)
router.include_router(products.router)
router.include_router(transactions.router)
router.include_router(dashboard.router)