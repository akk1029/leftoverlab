"""Recipe + saved-recipe models (FR06-FR08 / data rule 2.3)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RecipeCategory
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Recipe(Base):
    __tablename__ = "recipes"

    # RecipeID: 'REC' followed by 3 digits, e.g. REC001
    id: Mapped[str] = mapped_column(String(6), primary_key=True)

    # Author is optional: seeded/global recipes have no author.
    author_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[RecipeCategory] = mapped_column(
        Enum(RecipeCategory, native_enum=False, length=20), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Newline- or comma-separated; kept simple for a starter schema.
    ingredients_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")

    cooking_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Comma-separated dietary tags (e.g. "Vegan,Gluten-Free").
    dietary_tags: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    author: Mapped["User | None"] = relationship(back_populates="recipes")
    saved_by: Mapped[list["SavedRecipe"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class SavedRecipe(Base):
    """Join table for a user's saved/favourite recipes (FR08)."""

    __tablename__ = "saved_recipes"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_saved_user_recipe"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    recipe_id: Mapped[str] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="saved_recipes")
    recipe: Mapped["Recipe"] = relationship(back_populates="saved_by")
