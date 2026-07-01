"""Recipe CRUD, filtering, saving, and recommendation routes (FR06-FR08)."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_

from app.api.deps import CurrentUser, DbSession
from app.core.enums import RecipeCategory
from app.core.ids import next_id
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, SavedRecipe
from app.schemas.generate import GeneratedRecipe, GenerateResponse
from app.schemas.recipe import (
    RecipeCreate,
    RecipePublic,
    RecipeRecommendation,
    RecipeUpdate,
)
from app.services.dietary import parse_allergies
from app.services.themealdb import generate_from_inventory, lookup_meal

router = APIRouter(prefix="/recipes", tags=["recipes"])

# TheMealDB categories don't map 1:1 onto our meal-type enum; approximate.
_MEALDB_CATEGORY_MAP = {
    "Breakfast": RecipeCategory.BREAKFAST,
    "Dessert": RecipeCategory.DESSERT,
    "Starter": RecipeCategory.SNACK,
    "Side": RecipeCategory.SNACK,
}


def _map_category(mealdb_category: str | None) -> RecipeCategory:
    return _MEALDB_CATEGORY_MAP.get(mealdb_category or "", RecipeCategory.DINNER)


def _tokenize(text: str) -> set[str]:
    """Lower-cased ingredient tokens from a recipe's free-text ingredient list."""
    parts = re.split(r"[,\n;]+", text or "")
    return {p.strip().lower() for p in parts if p.strip()}


@router.post("", response_model=RecipePublic, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeCreate, db: DbSession, current_user: CurrentUser
) -> Recipe:
    recipe = Recipe(
        id=next_id(db, "REC", 3),
        author_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.get("", response_model=list[RecipePublic])
def list_recipes(
    db: DbSession,
    current_user: CurrentUser,
    category: RecipeCategory | None = None,
    max_cooking_time: int | None = Query(default=None, ge=0),
    max_cost: float | None = Query(default=None, ge=0),
    dietary_tag: str | None = Query(default=None, description="Filter by a dietary tag."),
    search: str | None = Query(default=None, description="Match title/description."),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Recipe]:
    """Recipe Filtering System (FR07)."""
    q = db.query(Recipe)
    if category is not None:
        q = q.filter(Recipe.category == category)
    if max_cooking_time is not None:
        q = q.filter(Recipe.cooking_time_minutes <= max_cooking_time)
    if max_cost is not None:
        q = q.filter(Recipe.estimated_cost <= max_cost)
    if dietary_tag:
        q = q.filter(Recipe.dietary_tags.ilike(f"%{dietary_tag}%"))
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Recipe.title.ilike(like), Recipe.description.ilike(like)))
    return q.order_by(Recipe.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/recommendations", response_model=list[RecipeRecommendation])
def recommend(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[RecipeRecommendation]:
    """Personalized Recipe Recommendation based on owned ingredients (FR06).

    Scores every recipe by the fraction of its ingredients the user already has,
    optionally constrained to their dietary preference, and returns the best matches.
    """
    owned = {
        i.name.strip().lower()
        for i in db.query(Ingredient).filter(Ingredient.owner_id == current_user.id).all()
    }

    pref = current_user.dietary_preference.value
    recipes = db.query(Recipe).all()

    scored: list[RecipeRecommendation] = []
    for recipe in recipes:
        if pref and pref != "None" and recipe.dietary_tags:
            if pref.lower() not in recipe.dietary_tags.lower():
                continue
        tokens = _tokenize(recipe.ingredients_text)
        if not tokens:
            continue
        matched = {t for t in tokens if any(t in o or o in t for o in owned)}
        missing = tokens - matched
        score = len(matched) / len(tokens)
        if score == 0:
            continue
        scored.append(
            RecipeRecommendation(
                recipe=RecipePublic.model_validate(recipe),
                match_score=round(score, 2),
                matched_ingredients=sorted(matched),
                missing_ingredients=sorted(missing),
            )
        )

    scored.sort(key=lambda r: r.match_score, reverse=True)
    return scored[:limit]


@router.get("/saved", response_model=list[RecipePublic])
def list_saved(db: DbSession, current_user: CurrentUser) -> list[Recipe]:
    """View saved recipe collection (FR08)."""
    rows = (
        db.query(Recipe)
        .join(SavedRecipe, SavedRecipe.recipe_id == Recipe.id)
        .filter(SavedRecipe.user_id == current_user.id)
        .order_by(SavedRecipe.saved_at.desc())
        .all()
    )
    return rows


@router.get("/generate", response_model=GenerateResponse)
async def generate_from_themealdb(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=25),
    respect_dietary: bool = Query(default=True, description="Honour the user's dietary preference."),
    respect_allergies: bool = Query(default=True, description="Exclude recipes with allergens."),
) -> GenerateResponse:
    """Generate real recipes from TheMealDB using the user's inventory (FR06).

    Only recipes compatible with the user's dietary preference and free of their
    declared allergens are returned, ranked by how much of each recipe you
    already have on hand.
    """
    inventory = [
        i.name for i in db.query(Ingredient).filter(Ingredient.owner_id == current_user.id).all()
    ]
    allergies = parse_allergies(current_user.allergies)

    meals = await generate_from_inventory(
        inventory,
        preference=current_user.dietary_preference,
        allergies=allergies,
        limit=limit,
        respect_dietary=respect_dietary,
        respect_allergies=respect_allergies,
    )
    return GenerateResponse(
        count=len(meals),
        dietary_preference=current_user.dietary_preference.value,
        allergies_applied=allergies if respect_allergies else [],
        recipes=[GeneratedRecipe(**vars(m)) for m in meals],
    )


@router.post("/generate/{mealdb_id}/import", response_model=RecipePublic, status_code=status.HTTP_201_CREATED)
async def import_generated_recipe(
    mealdb_id: str, db: DbSession, current_user: CurrentUser
) -> Recipe:
    """Import a TheMealDB recipe into the user's own collection (usable in
    saving, meal plans, and shopping-list generation)."""
    meal = await lookup_meal(mealdb_id)
    if meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found on TheMealDB.")

    # Fold TheMealDB tags + category into our comma-separated dietary_tags field.
    tags = list(meal.tags)
    if meal.category in ("Vegan", "Vegetarian") and meal.category not in tags:
        tags.append(meal.category)

    desc_bits = [b for b in (meal.area, meal.category) if b]
    recipe = Recipe(
        id=next_id(db, "REC", 3),
        author_id=current_user.id,
        title=meal.title,
        category=_map_category(meal.category),
        description=f"Imported from TheMealDB{(' · ' + ' · '.join(desc_bits)) if desc_bits else ''}."
        + (f" Source: {meal.source_url}" if meal.source_url else ""),
        ingredients_text="\n".join(meal.ingredients),
        instructions=meal.instructions,
        dietary_tags=",".join(tags) if tags else None,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.get("/{recipe_id}", response_model=RecipePublic)
def get_recipe(recipe_id: str, db: DbSession, current_user: CurrentUser) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    return recipe


@router.patch("/{recipe_id}", response_model=RecipePublic)
def update_recipe(
    recipe_id: str,
    payload: RecipeUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    if recipe.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your recipe.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(recipe, field, value)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_recipe(recipe_id: str, db: DbSession, current_user: CurrentUser) -> None:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    if recipe.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your recipe.")
    db.delete(recipe)
    db.commit()


@router.post("/{recipe_id}/save", status_code=status.HTTP_201_CREATED)
def save_recipe(recipe_id: str, db: DbSession, current_user: CurrentUser) -> dict:
    """Save a favourite recipe (FR08)."""
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    existing = (
        db.query(SavedRecipe)
        .filter(SavedRecipe.user_id == current_user.id, SavedRecipe.recipe_id == recipe_id)
        .first()
    )
    if existing:
        return {"detail": "Already saved.", "recipe_id": recipe_id}
    db.add(SavedRecipe(user_id=current_user.id, recipe_id=recipe_id))
    db.commit()
    return {"detail": "Saved.", "recipe_id": recipe_id}


@router.delete("/{recipe_id}/save", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def unsave_recipe(recipe_id: str, db: DbSession, current_user: CurrentUser) -> None:
    row = (
        db.query(SavedRecipe)
        .filter(SavedRecipe.user_id == current_user.id, SavedRecipe.recipe_id == recipe_id)
        .first()
    )
    if row:
        db.delete(row)
        db.commit()
