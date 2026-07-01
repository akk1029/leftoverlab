"""Recipe schemas (data rule 2.3)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RecipeCategory


class RecipeBase(BaseModel):
    title: str = Field(..., max_length=200)
    category: RecipeCategory
    description: str | None = None
    ingredients_text: str = Field(default="", description="One ingredient per line or comma-separated.")
    instructions: str = ""
    cooking_time_minutes: int | None = Field(default=None, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0)
    dietary_tags: str | None = Field(default=None, max_length=200)


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    category: RecipeCategory | None = None
    description: str | None = None
    ingredients_text: str | None = None
    instructions: str | None = None
    cooking_time_minutes: int | None = Field(default=None, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0)
    dietary_tags: str | None = Field(default=None, max_length=200)


class RecipePublic(RecipeBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    author_id: str | None
    created_at: datetime


class RecipeRecommendation(BaseModel):
    """A recipe plus why it was recommended (FR06)."""

    recipe: RecipePublic
    match_score: float = Field(..., description="0..1 fraction of recipe ingredients you already have.")
    matched_ingredients: list[str]
    missing_ingredients: list[str]
