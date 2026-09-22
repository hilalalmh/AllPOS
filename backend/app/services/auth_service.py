from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.user_repository import UserRepository


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class UserInactiveError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, username: str, password: str) -> User:
        user = self.users.get_by(username=username)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Username atau password salah.")
        if not user.is_active:
            raise UserInactiveError("Akun tidak aktif.")
        return user

    def issue_tokens(self, user: User) -> dict:
        access, exp_in = create_access_token(user.id)
        refresh, _ = create_refresh_token(user.id)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": exp_in,
        }

    def refresh(self, refresh_token: str) -> dict:
        user_id = decode_token(refresh_token, "refresh")
        if user_id is None:
            raise InvalidRefreshTokenError("Refresh token tidak valid.")
        user = self.users.get(user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError("Refresh token tidak valid.")
        return self.issue_tokens(user)


def create_user(
    db: Session,
    role_id: int,
    username: str,
    password: str,
    full_name: str,
) -> User:
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(db)
    user = User(
        role_id=role_id,
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
    )
    repo.add(user, flush=True)
    return user