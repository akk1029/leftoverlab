"""User & auth schemas (data rule 2.1)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import DietaryPreference
from app.schemas.validators import validate_password


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=120)
    dietary_preference: DietaryPreference = DietaryPreference.NONE
    allergies: str | None = Field(
        default=None, max_length=500, description="Comma-separated list of allergies."
    )


class UserCreate(UserBase):
    password: str = Field(..., description="Min 8 chars, 1 uppercase, 1 number, 1 special.")

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password(v)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    dietary_preference: DietaryPreference | None = None
    allergies: str | None = Field(default=None, max_length=500)


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime


# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
