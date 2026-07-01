"""Sustainability dashboard records (FR13 / data rule 2.4)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class SustainabilityRecord(Base):
    """A single logged food-saving event used to power the dashboard stats."""

    __tablename__ = "sustainability_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # What was saved (e.g. an ingredient name or recipe used up leftovers).
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    money_saved: Mapped[float] = mapped_column(Float, nullable=False)  # positive
    carbon_reduction_kg: Mapped[float] = mapped_column(Float, nullable=False)  # positive, kg CO2e
    food_saved_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="sustainability_records")
