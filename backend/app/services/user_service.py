from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password, verify_password
from app.models import Role, RoleEnum, User
from app.services.auth_service import create_user


class UserNotFoundError(Exception):
    pass


class UsernameTakenError(Exception):
    pass


class LastOwnerError(Exception):
    pass


class SelfRoleChangeError(Exception):
    pass


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def list_users(
        self, *, q: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        filters = []
        if q:
            pattern = f"%{q.strip()}%"
            filters.append(
                func.lower(User.username).like(pattern.lower())
                | func.lower(User.full_name).like(pattern.lower())
            )
        total = self.db.scalar(
            select(func.count(User.id)).where(*filters)
        ) or 0
        stmt = (
            select(User)
            .options(joinedload(User.role))
            .where(*filters)
            .order_by(User.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).all())
        return items, total

    def get_user(self, user_id: int) -> User:
        user = self.db.scalar(
            select(User).options(joinedload(User.role)).where(User.id == user_id)
        )
        if user is None:
            raise UserNotFoundError("Pengguna tidak ditemukan.")
        return user

    def create(self, payload) -> User:
        existing = self.db.scalar(
            select(User).where(func.lower(User.username) == payload.username.lower())
        )
        if existing is not None:
            raise UsernameTakenError("Username sudah digunakan.")
        role = self.db.scalar(select(Role).where(Role.name == payload.role))
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Role tidak dikenal.",
            )
        return create_user(
            self.db,
            role_id=role.id,
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
        )

    def update(self, actor: User, user_id: int, payload) -> User:
        user = self.get_user(user_id)
        data = payload.model_dump(exclude_unset=True)

        if data.get("password"):
            user.password_hash = hash_password(data["password"])
        data.pop("password", None)

        if data.get("full_name"):
            user.full_name = data["full_name"]

        if data.get("is_active") is False and user.id == actor.id:
            raise SelfRoleChangeError(
                "Tidak bisa menonaktifkan akun sendiri."
            )

        if data.get("role") is not None:
            if user.id == actor.id and data["role"] != RoleEnum.OWNER.value:
                raise SelfRoleChangeError(
                    "Tidak bisa menurunkan role diri sendiri."
                )
            new_role = self.db.scalar(
                select(Role).where(Role.name == data["role"])
            )
            if new_role is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Role tidak dikenal.",
                )
            user.role_id = new_role.id

        if data.get("is_active") is False:
            user.is_active = False
        elif data.get("is_active") is True:
            user.is_active = True

        try:
            self.db.flush()
            self._ensure_owner_remaining(user)
        except LastOwnerError:
            self.db.rollback()
            raise
        return user

    def _ensure_owner_remaining(self, user: User) -> None:
        """Pastikan selalu ada minimal satu OWNER aktif setelah perubahan.

        SELECT … FOR UPDATE mengunci baris OWNER sehingga dua proses yang
        menurunkan role/nonaktifkan OWNER tidak bisa melewati guard secara
        bersamaan (transaksi kedua menunggu dan melihat hasil commit yang baru).
        """
        owner_role_id = self.db.scalar(
            select(Role.id).where(Role.name == RoleEnum.OWNER.value)
        )
        owner_ids = self.db.scalars(
            select(User.id)
            .where(
                User.role_id == owner_role_id,
                User.is_active.is_(True),
            )
            .with_for_update()
        ).all()
        if not owner_ids:
            raise LastOwnerError(
                "Harus selalu ada minimal satu OWNER yang aktif."
            )

    def change_own_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password saat ini salah.",
            )
        user.password_hash = hash_password(new_password)
        self.db.flush()
