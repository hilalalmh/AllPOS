from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class UserAdminOut(UserOut):
    role: str


class UserList(BaseModel):
    items: list[UserAdminOut]
    total: int
    page: int
    page_size: int


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    role: Literal["OWNER", "KASIR"] = "KASIR"


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: Literal["OWNER", "KASIR"] | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)