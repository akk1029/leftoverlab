"""Schemas for inventory-based recipe generation via TheMealDB."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratedRecipe(BaseModel):
    id: str = Field(..., description="Namespaced id, e.g. 'themealdb:52772'.")
    mealdb_id: str
    source: str = "TheMealDB"
    title: str
    category: str | None = None
    area: str | None = None
    thumbnail: str | None = None
    source_url: str | None = None
    youtube_url: str | None = None
    instructions: str = ""
    tags: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    match_score: float = Field(..., description="Fraction of recipe ingredients you already have (0..1).")
    matched_ingredients: list[str] = Field(default_factory=list)
    missing_ingredients: list[str] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    count: int
    dietary_preference: str
    allergies_applied: list[str]
    recipes: list[GeneratedRecipe]
