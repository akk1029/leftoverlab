"""Meal planner schemas (FR12)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recipe import RecipePublic


class MealPlanEntryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_offset: int
    meal_slot: str
    recipe: RecipePublic | None = None


class MealPlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: str
    name: str
    week_start: date
    created_at: datetime
    entries: list[MealPlanEntryPublic] = Field(default_factory=list)


class GenerateMealPlanRequest(BaseModel):
    """Generate a weekly plan, prioritising soon-to-expire ingredients (FR12)."""

    week_start: str = Field(..., description="Start date as DD/MM/YYYY.")
    name: str = Field(default="Weekly Plan", max_length=120)
    meals_per_day: list[str] = Field(
        default_factory=lambda: ["Breakfast", "Lunch", "Dinner"]
    )
    days: int = Field(default=7, ge=1, le=14)
    # Only consider recipes matching the user's dietary preference.
    respect_dietary_preference: bool = True
