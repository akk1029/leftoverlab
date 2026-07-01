"""Shopping list schemas (data rule 2.4)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShoppingListItemBase(BaseModel):
    name: str = Field(..., max_length=120)
    quantity: float = Field(default=1.0, gt=0)
    unit: str | None = Field(default=None, max_length=30)


class ShoppingListItemCreate(ShoppingListItemBase):
    pass


class ShoppingListItemUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=30)
    is_purchased: bool | None = None


class ShoppingListItemPublic(ShoppingListItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_purchased: bool


class ShoppingListCreate(BaseModel):
    name: str = Field(default="My Shopping List", max_length=120)
    items: list[ShoppingListItemCreate] = Field(default_factory=list)


class ShoppingListPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    created_at: datetime
    items: list[ShoppingListItemPublic] = Field(default_factory=list)


class GenerateFromRecipesRequest(BaseModel):
    """Auto-generate a shopping list from chosen recipes (FR11)."""

    recipe_ids: list[str] = Field(..., min_length=1)
    name: str = Field(default="Generated Shopping List", max_length=120)
    # If true, ingredients already in the user's inventory are excluded.
    exclude_owned: bool = True
