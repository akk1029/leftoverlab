"""User model (FR01, FR02 / data rule 2.1)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import DietaryPreference
from app.database import Base

if TYPE_CHECKING:
    from app.models.community import Comment, Post
    from app.models.ingredient import Ingredient
    from app.models.mealplan import MealPlan
    from app.models.recipe import SavedRecipe
    from app.models.shopping import ShoppingList
    from app.models.sustainability import SustainabilityRecord


class User(Base):
    __tablename__ = "users"

    # UserID: 'U' followed by exactly 3 digits, e.g. U001
    id: Mapped[str] = mapped_column(String(4), primary_key=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    dietary_preference: Mapped[DietaryPreference] = mapped_column(
        Enum(DietaryPreference, native_enum=False, length=20),
        default=DietaryPreference.NONE,
        nullable=False,
    )
    # Free-text list of allergies, stored comma-separated.
    allergies: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    ingredients: Mapped[list["Ingredient"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    recipes: Mapped[list["Recipe"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="author", cascade="all, delete-orphan"
    )
    saved_recipes: Mapped[list["SavedRecipe"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    shopping_lists: Mapped[list["ShoppingList"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    meal_plans: Mapped[list["MealPlan"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    sustainability_records: Mapped[list["SustainabilityRecord"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
