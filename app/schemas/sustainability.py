"""Sustainability dashboard schemas (FR13 / data rule 2.4)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SustainabilityRecordCreate(BaseModel):
    description: str | None = Field(default=None, max_length=200)
    money_saved: float = Field(..., gt=0, description="Positive amount of money saved.")
    carbon_reduction_kg: float = Field(
        ..., gt=0, description="Positive kg CO2e reduction."
    )
    food_saved_kg: float = Field(default=0.0, ge=0)


class SustainabilityRecordPublic(SustainabilityRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: str
    created_at: datetime


class SustainabilityDashboard(BaseModel):
    """Aggregated stats for the dashboard view."""

    total_money_saved: float
    total_carbon_reduction_kg: float
    total_food_saved_kg: float
    records_count: int
    achievements: list[str]
