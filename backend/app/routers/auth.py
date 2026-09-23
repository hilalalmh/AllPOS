import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserMe
from app.services.audit_service import record_audit
from app.services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserInactiveError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_login_attempts: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_login_lock = Lock()


def _check_login_throttle(username: str, client_ip: str) -> None:
    key = (username.lower(), client_ip)
    window = settings.LOGIN_LOCKOUT_MINUTES * 60
    now = time.monotonic()
    with _login_lock:
        attempts = _login_attempts[key]
        while attempts and now - attempts[0] > window:
            attempts.popleft()
        if len(attempts) >= settings.LOGIN_MAX_FAILURES:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Terlalu banyak percobaan login. Coba lagi nanti.",
                headers={"Retry-After": str(settings.LOGIN_LOCKOUT_MINUTES * 60)},
            )
        attempts.append(now)


def _register_login_success(username: str, client_ip: str) -> None:
    with _login_lock:
        _login_attempts.pop((username.lower(), client_ip), None)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    _check_login_throttle(payload.username, client_ip)
    service = AuthService(db)
    try:
        user = service.authenticate(payload.username, payload.password)
        tokens = service.issue_tokens(user)
        _register_login_success(payload.username, client_ip)
        record_audit(
            db,
            user=user,
            action="auth.login",
            entity_type="user",
            entity_id=user.id,
            details={"username": user.username},
        )
        db.commit()
        return tokens
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        return service.refresh(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    AuthService(db).revoke(payload.refresh_token)
    db.commit()


@router.get("/me", response_model=UserMe)
def me(current_user: User = Depends(get_current_user)):
    return UserMe(
        id=current_user.id,
        role_id=current_user.role_id,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        role=current_user.role.name,
    )