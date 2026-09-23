from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token_payload,
    hash_password,
    verify_password,
)
from app.models import RefreshToken, User
from app.repositories.user_repository import UserRepository


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class UserInactiveError(Exception):
    pass


# Hash bcrypt untuk string dummy; dipakai saat username tidak ditemukan agar
# waktu verifikasi serupa dengan username yang ada (anti username enumeration).
_DUMMY_BCRYPT_HASH = (
    "$2b$12$UNaQ.fIOEf0B0SCYFZIBZeunBjt79BWlhOaWsgHmc1LJtEqcUUngi"
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, username: str, password: str) -> User:
        user = self.users.get_by(username=username)
        # Username yang hilang tetap memverifikasi bcrypt dummy agar waktu
        # respons tidak membedakan akun yang ada vs tidak ada (anti-enumeration).
        if user is None:
            verify_password(password, _DUMMY_BCRYPT_HASH)
            raise InvalidCredentialsError("Username atau password salah.")
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Username atau password salah.")
        if not user.is_active:
            raise UserInactiveError("Akun tidak aktif.")
        return user

    def issue_tokens(self, user: User) -> dict:
        access, exp_in = create_access_token(user.id)
        refresh, jti = create_refresh_token(user.id)
        self.db.add(
            RefreshToken(
                jti=jti,
                user_id=user.id,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.JWT_REFRESH_EXPIRES_DAYS),
            )
        )
        self._purge_expired_tokens(user.id)
        self.db.flush()
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": exp_in,
        }

    def refresh(self, refresh_token: str) -> dict:
        payload = decode_token_payload(refresh_token, REFRESH_TOKEN_TYPE)
        if payload is None:
            raise InvalidRefreshTokenError("Refresh token tidak valid.")
        try:
            user_id = int(payload["sub"])
            jti = str(payload["jti"])
        except (KeyError, TypeError, ValueError):
            raise InvalidRefreshTokenError("Refresh token tidak valid.")

        user = self.users.get(user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError("Refresh token tidak valid.")

        # Rotasi atomik: UPDATE dengan filter revoked=False memberi row count 1
        # hanya untuk pemenang perlombaan. Refresh bersamaan dengan token sama
        # akan mendapat rowcount 0 dan ditolak, sehingga token lama tak bisa
        # dipakai dua kali (replay).
        rotated = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.jti == jti,
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .update({"revoked": True}, synchronize_session=False)
        )
        if rotated != 1:
            raise InvalidRefreshTokenError("Refresh token tidak valid.")
        return self.issue_tokens(user)

    def revoke_all_for_user(self, user_id: int) -> int:
        """Cabut semua refresh token milik user (mis. saat ganti password)."""
        return (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .update({"revoked": True}, synchronize_session=False)
        )

    def revoke(self, refresh_token: str) -> bool:
        """Cabut refresh token bila dikenali (idempoten)."""
        payload = decode_token_payload(refresh_token, REFRESH_TOKEN_TYPE)
        if payload is None:
            return False
        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti or not sub:
            return False
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            return False
        record = (
            self.db.query(RefreshToken).filter_by(jti=jti).one_or_none()
        )
        if record is None or record.user_id != user_id:
            return False
        record.revoked = True
        return True

    def _purge_expired_tokens(self, user_id: int) -> None:
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at < datetime.now(timezone.utc),
        ).delete(synchronize_session=False)


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