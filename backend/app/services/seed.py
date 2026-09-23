from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import (
    Category,
    Product,
    Role,
    RoleEnum,
    StoreProfile,
    User,
)
from app.repositories.role_repository import RoleRepository
from app.services.auth_service import create_user

DEFAULT_OWNER_USERNAME = "owner"
SEED_ADMIN_PASSWORD = settings.SEED_ADMIN_PASSWORD


def seed_roles(db: Session) -> dict[str, Role]:
    roles_by_name: dict[str, Role] = {}
    for role_enum in RoleEnum:
        role = db.query(Role).filter_by(name=role_enum.value).first()
        if role is None:
            role = Role(name=role_enum.value, is_active=True)
            db.add(role)
        roles_by_name[role_enum.value] = role
    db.flush()
    return roles_by_name


def seed_store_profile(db: Session) -> None:
    """Pastikan singleton profil toko (id=1) ada dengan default."""
    profile = db.get(StoreProfile, 1)
    if profile is None:
        db.add(
            StoreProfile(
                id=1,
                store_name="SISTEM POS",
                address=None,
                phone=None,
                footer="TERIMA KASIH ~ SILAHKAN DATANG KEMBALI",
            )
        )
        db.flush()


def seed_admin_user(db: Session) -> None:
    repo = RoleRepository(db)
    owner_role = repo.get_by(name=RoleEnum.OWNER.value)
    if owner_role is None:
        raise RuntimeError("Role OWNER belum ada. Seed roles terlebih dahulu.")

    existing = db.query(User).filter_by(username=DEFAULT_OWNER_USERNAME).first()
    if existing is not None:
        return

    create_user(
        db,
        role_id=owner_role.id,
        username=DEFAULT_OWNER_USERNAME,
        password=SEED_ADMIN_PASSWORD,
        full_name="Owner",
    )


DEMO_CATEGORIES = {
    "Coffee": [
        ("Es Kopi", 18000, "ESKOPI"),
        ("Americano", 15000, "AMERICANO"),
        ("Latte", 20000, "LATTE"),
    ],
    "Non Coffee": [
        ("Matcha", 22000, "MATCHA"),
        ("Chocolate", 20000, "CHOCO"),
        ("Tea", 12000, "TEALEMON"),
    ],
}


def seed_demo_products(db: Session) -> None:
    if db.query(Category).count() > 0:
        return

    for cat_name, products in DEMO_CATEGORIES.items():
        category = Category(name=cat_name, is_active=True)
        db.add(category)
        db.flush()
        for name, price, sku in products:
            db.add(
                Product(
                    category_id=category.id,
                    name=name,
                    sku=sku,
                    price=price,
                    description=None,
                    is_active=True,
                )
            )
    db.flush()


def run_seed() -> None:
    with SessionLocal() as db:
        try:
            seed_roles(db)
            seed_admin_user(db)
            seed_store_profile(db)
            seed_demo_products(db)
            db.commit()
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    run_seed()
    print("Seed berhasil: roles OWNER/KASIR + admin 'owner' + profil toko + contoh produk.")
