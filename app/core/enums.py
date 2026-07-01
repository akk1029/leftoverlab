"""Enumerations enforced by the data-validation rules (section 2)."""
from __future__ import annotations

import enum


class DietaryPreference(str, enum.Enum):
    VEGETARIAN = "Vegetarian"
    VEGAN = "Vegan"
    HALAL = "Halal"
    GLUTEN_FREE = "Gluten-Free"
    NONE = "None"


class RecipeCategory(str, enum.Enum):
    BREAKFAST = "Breakfast"
    LUNCH = "Lunch"
    DINNER = "Dinner"
    SNACK = "Snack"
    DESSERT = "Dessert"
