"""Ingredient schemas (data rule 2.2)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.schemas.validators import format_date, parse_future_date


class IngredientBase(BaseModel):
    name: str = Field(..., max_length=120)
    quantity: float = Field(..., gt=0, description="Must be strictly greater than zero.")
    unit: str | None = Field(default=None, max_length=30)
    storage_location: str | None = Field(default=None, max_length=60)


class IngredientCreate(IngredientBase):
    # Accept DD/MM/YYYY string; validated to be a future date.
    expiry_date: str = Field(..., description="Future date as DD/MM/YYYY.")

    @field_validator("expiry_date")
    @classmethod
    def _check_expiry(cls, v: str) -> date:  # type: ignore[override]
        return parse_future_date(v)


class IngredientUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=30)
    storage_location: str | None = Field(default=None, max_length=60)
    expiry_date: str | None = Field(default=None, description="Future date as DD/MM/YYYY.")

    @field_validator("expiry_date")
    @classmethod
    def _check_expiry(cls, v: str | None) -> date | None:  # type: ignore[override]
        if v is None:
            return None
        return parse_future_date(v)


class IngredientPublic(IngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    source: str
    created_at: datetime
    # Stored as a date; expose formatted + a days-left convenience field.
    expiry_date: date = Field(exclude=True)

    @computed_field
    @property
    def expiry_date_display(self) -> str:
        return format_date(self.expiry_date)

    @computed_field
    @property
    def days_until_expiry(self) -> int:
        return (self.expiry_date - date.today()).days
