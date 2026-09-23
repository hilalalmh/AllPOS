from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

_WEAK_SECRETS = {"change-me-in-production", "dev-secret-change-me", "secret"}


def assert_secure_config() -> None:
    """Fail fast di lingkungan produksi bila secret lemah/default."""
    if settings.ENVIRONMENT != "production":
        return
    if (
        not settings.JWT_SECRET
        or len(settings.JWT_SECRET) < 32
        or settings.JWT_SECRET in _WEAK_SECRETS
    ):
        raise RuntimeError(
            "JWT_SECRET harus minimal 32 karakter acak saat ENVIRONMENT=production."
        )
    if settings.SEED_ADMIN_PASSWORD == "admin123":
        raise RuntimeError(
            "SEED_ADMIN_PASSWORD masih default (admin123). Ganti sebelum produksi."
        )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(
        payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )


def create_access_token(user_id: int) -> tuple[str, int]:
    expires = timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    token = _create_token(str(user_id), ACCESS_TOKEN_TYPE, expires)
    return token, int(expires.total_seconds())


def create_refresh_token(user_id: int) -> tuple[str, int]:
    expires = timedelta(days=settings.JWT_REFRESH_EXPIRES_DAYS)
    token = _create_token(str(user_id), REFRESH_TOKEN_TYPE, expires)
    return token, int(expires.total_seconds())


def decode_token(token: str, expected_type: str) -> int | None:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.InvalidTokenError:
        return None
    if payload.get("type") != expected_type:
        return None
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None