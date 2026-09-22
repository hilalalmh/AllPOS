from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role_id: int
    username: str
    full_name: str
    is_active: bool
    created_at: datetime


class UserMe(UserOut):
    role: str