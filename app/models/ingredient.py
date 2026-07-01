"""Ingredient inventory model (FR03-FR05, FR09 / data rule 2.2)."""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Ingredient(Base):
    __tablename__ = "ingredients"

    # IngredientID: 'ING' followed by 3 digits, e.g. ING001
    id: Mapped[str] = mapped_column(String(6), primary_key=True)

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)  # strictly > 0
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Provenance: "manual", "image_upload", "camera"
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    storage_location: Mapped[str | None] = mapped_column(String(60), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="ingredients")
