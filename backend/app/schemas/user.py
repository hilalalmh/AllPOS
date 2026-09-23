from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# bcrypt hanya memproses 72 byte pertama; password lebih panjang diam-diam
# terpotong hingga berbenturan dengan password lain yang memiliki awalan sama.
BCRYPT_MAX_BYTES = 72


def _ensure_bcrypt_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError(
            f"Password maksimal {BCRYPT_MAX_BYTES} byte (UTF-8)."
        )
    return value


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

    _password_bytes = field_validator("password")(_ensure_bcrypt_bytes)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: Literal["OWNER", "KASIR"] | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)

    _password_bytes = field_validator("password")(_ensure_bcrypt_bytes)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)

    _new_password_bytes = field_validator("new_password")(_ensure_bcrypt_bytes)