from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import RoleEnum, User
from app.schemas.store_profile import StoreProfileOut, StoreProfileUpdate
from app.services.audit_service import record_audit
from app.services.store_profile_service import StoreProfileService

router = APIRouter(prefix="/store-profile", tags=["store-profile"])


def _get_service(db: Session = Depends(get_db)) -> StoreProfileService:
    return StoreProfileService(db)


@router.get("", response_model=StoreProfileOut)
def get_store_profile(
    service: StoreProfileService = Depends(_get_service),
    _: object = Depends(get_current_user),
):
    """Ambil profil toko (singleton). Akses: semua role terautentikasi."""
    try:
        return service.get_profile()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Gagal memuat profil: {exc}") from exc


@router.put("", response_model=StoreProfileOut)
def update_store_profile(
    payload: StoreProfileUpdate,
    service: StoreProfileService = Depends(_get_service),
    current_user: User = Depends(require_roles(RoleEnum.OWNER)),
):
    """Perbarui profil toko (nama, alamat, telp, footer struk). Hanya OWNER."""
    try:
        profile = service.update_profile(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Gagal menyimpan profil: {exc}") from exc
    record_audit(
        service.db,
        user=current_user,
        action="store_profile.update",
        entity_type="store_profile",
        entity_id=profile.id,
        details={"store_name": profile.store_name, "updated": list(payload.model_dump(exclude_unset=True).keys())},
    )
    service.db.flush()
    return profile

