from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StoreProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_name: str
    address: str | None = None
    phone: str | None = None
    footer: str
    created_at: datetime
    updated_at: datetime


class StoreProfileUpdate(BaseModel):
    """Update parsial — semua field opsional; hanya yang dikirim yang diubah."""

    store_name: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    footer: str | None = Field(default=None, min_length=1, max_length=120)
