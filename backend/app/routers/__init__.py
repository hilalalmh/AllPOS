from fastapi import APIRouter

from app.routers import (
    audit,
    auth,
    categories,
    dashboard,
    health,
    products,
    reports,
    store_profile,
    transactions,
)

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router)
router.include_router(categories.router)
router.include_router(products.router)
router.include_router(transactions.router)
router.include_router(dashboard.router)
router.include_router(store_profile.router)
router.include_router(audit.router)
router.include_router(reports.router)