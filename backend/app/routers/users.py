from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import RoleEnum, User
from app.schemas.user import (
    PasswordChange,
    UserAdminOut,
    UserCreate,
    UserList,
    UserUpdate,
)
from app.services.audit_service import record_audit
from app.services.user_service import (
    LastOwnerError,
    SelfRoleChangeError,
    UsernameTakenError,
    UserNotFoundError,
    UserService,
)

router = APIRouter(prefix="/users", tags=["users"])


def _get_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("", response_model=UserList)
def list_users(
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: UserService = Depends(_get_service),
    _: User = Depends(require_roles(RoleEnum.OWNER)),
):
    items, total = service.list_users(q=q, page=page, page_size=page_size)
    return UserList(
        items=[
            UserAdminOut(
                id=u.id,
                role_id=u.role_id,
                username=u.username,
                full_name=u.full_name,
                is_active=u.is_active,
                created_at=u.created_at,
                role=u.role.name,
            )
            for u in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=UserAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def create_user_endpoint(
    payload: UserCreate,
    service: UserService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
    db: Session = Depends(get_db),
):
    try:
        user = service.create(payload)
    except UsernameTakenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username sudah digunakan (duplikat).",
        )
    record_audit(
        db,
        user=current_user,
        action="user.create",
        entity_type="user",
        entity_id=user.id,
        details={"username": user.username, "role": payload.role},
    )
    db.flush()
    return UserAdminOut(
        id=user.id,
        role_id=user.role_id,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        role=payload.role,
    )


@router.put("/{user_id}", response_model=UserAdminOut)
def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
    db: Session = Depends(get_db),
):
    try:
        user = service.update(current_user, user_id, payload)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LastOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except SelfRoleChangeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    changed = payload.model_dump(exclude_unset=True).keys() - {"password"}
    record_audit(
        db,
        user=current_user,
        action="user.update",
        entity_type="user",
        entity_id=user.id,
        details={
            "username": user.username,
            "changed": sorted(changed),
            "password_changed": "password"
            in payload.model_dump(exclude_unset=True),
        },
    )
    db.flush()
    db.refresh(user)
    return UserAdminOut(
        id=user.id,
        role_id=user.role_id,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        role=user.role.name,
    )


@router.put("/me/password")
def change_own_password(
    payload: PasswordChange,
    service: UserService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER, RoleEnum.KASIR)),
    db: Session = Depends(get_db),
):
    service.change_own_password(
        current_user, payload.current_password, payload.new_password
    )
    record_audit(
        db,
        user=current_user,
        action="user.password_change",
        entity_type="user",
        entity_id=current_user.id,
        details={"username": current_user.username},
    )
    db.commit()
    return {"detail": "Password berhasil diubah."}
