"""Seed the database with a handful of global recipes.

Run locally with:  python -m scripts.seed
Idempotent: skips seeding if recipes already exist.
"""
from __future__ import annotations

from app.core.enums import RecipeCategory
from app.core.ids import next_id
from app.database import Base, SessionLocal, engine
from app.models.recipe import Recipe

SAMPLE_RECIPES = [
    {
        "title": "Veggie Omelette",
        "category": RecipeCategory.BREAKFAST,
        "description": "A quick protein-packed breakfast using up odd vegetables.",
        "ingredients_text": "Egg\nOnion\nBell Pepper\nCheese\nSpinach",
        "instructions": "Whisk eggs.\nSaute veggies.\nPour eggs over, add cheese, fold and serve.",
        "cooking_time_minutes": 10,
        "estimated_cost": 2.5,
        "dietary_tags": "Vegetarian,Gluten-Free",
    },
    {
        "title": "Garlic Tomato Pasta",
        "category": RecipeCategory.DINNER,
        "description": "Simple weeknight pasta from pantry staples.",
        "ingredients_text": "Pasta\nTomato\nGarlic\nOnion",
        "instructions": "Boil pasta.\nSaute garlic and onion.\nAdd tomato, simmer, toss with pasta.",
        "cooking_time_minutes": 20,
        "estimated_cost": 3.0,
        "dietary_tags": "Vegan,Vegetarian",
    },
    {
        "title": "Chicken & Rice Bowl",
        "category": RecipeCategory.LUNCH,
        "description": "Balanced bowl that uses leftover cooked chicken.",
        "ingredients_text": "Chicken\nRice\nCarrot\nBroccoli",
        "instructions": "Cook rice.\nStir-fry chicken and veg.\nCombine and season.",
        "cooking_time_minutes": 25,
        "estimated_cost": 4.0,
        "dietary_tags": "Halal,Gluten-Free",
    },
    {
        "title": "Banana Oat Snack",
        "category": RecipeCategory.SNACK,
        "description": "Use up overripe bananas.",
        "ingredients_text": "Banana\nMilk",
        "instructions": "Mash banana with oats.\nBake or microwave into bites.",
        "cooking_time_minutes": 15,
        "estimated_cost": 1.5,
        "dietary_tags": "Vegetarian",
    },
    {
        "title": "Mushroom Spinach Risotto",
        "category": RecipeCategory.DINNER,
        "description": "Creamy comfort food rescuing wilting spinach.",
        "ingredients_text": "Rice\nMushroom\nSpinach\nGarlic\nCheese",
        "instructions": "Saute mushrooms and garlic.\nAdd rice and stock gradually.\nFold in spinach and cheese.",
        "cooking_time_minutes": 35,
        "estimated_cost": 5.0,
        "dietary_tags": "Vegetarian",
    },
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Recipe).count() > 0:
            print("Recipes already present; skipping seed.")
            return
        for data in SAMPLE_RECIPES:
            recipe = Recipe(id=next_id(db, "REC", 3), author_id=None, **data)
            db.add(recipe)
        db.commit()
        print(f"Seeded {len(SAMPLE_RECIPES)} recipes.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
