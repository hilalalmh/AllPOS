from sqlalchemy.orm import Session

from app.models import StoreProfile
from app.schemas.store_profile import StoreProfileUpdate

DEFAULT_STORE_NAME = "SISTEM POS"
DEFAULT_FOOTER = "TERIMA KASIH ~ SILAHKAN DATANG KEMBALI"


class StoreProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self) -> StoreProfile:
        profile = self.db.get(StoreProfile, 1)
        if profile is None:
            profile = StoreProfile(
                id=1,
                store_name=DEFAULT_STORE_NAME,
                footer=DEFAULT_FOOTER,
            )
            self.db.add(profile)
            self.db.flush()
        return profile

    def update_profile(self, payload: StoreProfileUpdate) -> StoreProfile:
        profile = self.get_profile()
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile
