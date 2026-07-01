"""Smart meal planner routes (FR12)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.models.ingredient import Ingredient
from app.models.mealplan import MealPlan, MealPlanEntry
from app.models.recipe import Recipe
from app.schemas.mealplan import GenerateMealPlanRequest, MealPlanPublic
from app.api.routes.recipes import _tokenize  # reuse ingredient tokenizer

router = APIRouter(prefix="/meal-plans", tags=["meal-plan"])


def _get_owned(db: DbSession, plan_id: int, owner_id: str) -> MealPlan:
    plan = db.get(MealPlan, plan_id)
    if plan is None or plan.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found.")
    return plan


@router.post("/generate", response_model=MealPlanPublic, status_code=status.HTTP_201_CREATED)
def generate(
    payload: GenerateMealPlanRequest, db: DbSession, current_user: CurrentUser
) -> MealPlan:
    """Generate a weekly plan, prioritising recipes that use soon-to-expire stock (FR12)."""
    # week_start may legitimately be today, so parse without the "future date" constraint.
    from datetime import datetime

    try:
        week_start = datetime.strptime(payload.week_start, "%d/%m/%Y").date()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="week_start must be DD/MM/YYYY.",
        ) from exc

    # Rank the user's ingredients by soonest expiry.
    ingredients = (
        db.query(Ingredient)
        .filter(Ingredient.owner_id == current_user.id)
        .order_by(Ingredient.expiry_date.asc())
        .all()
    )
    owned = {i.name.strip().lower() for i in ingredients}

    pref = current_user.dietary_preference.value
    recipes = db.query(Recipe).all()

    def score(recipe: Recipe) -> float:
        tokens = _tokenize(recipe.ingredients_text)
        if not tokens:
            return 0.0
        matched = sum(1 for t in tokens if any(t in o or o in t for o in owned))
        return matched / len(tokens)

    # Filter by dietary preference, then sort best-match first.
    candidates = [
        r
        for r in recipes
        if not (
            payload.respect_dietary_preference
            and pref
            and pref != "None"
            and r.dietary_tags
            and pref.lower() not in r.dietary_tags.lower()
        )
    ]
    candidates.sort(key=score, reverse=True)

    plan = MealPlan(owner_id=current_user.id, name=payload.name, week_start=week_start)
    db.add(plan)
    db.flush()

    if candidates:
        idx = 0
        for day in range(payload.days):
            for slot in payload.meals_per_day:
                recipe = candidates[idx % len(candidates)]
                plan.entries.append(
                    MealPlanEntry(day_offset=day, meal_slot=slot, recipe_id=recipe.id)
                )
                idx += 1
    else:
        # No recipes yet — still create empty slots so the client can fill them in.
        for day in range(payload.days):
            for slot in payload.meals_per_day:
                plan.entries.append(MealPlanEntry(day_offset=day, meal_slot=slot, recipe_id=None))

    db.commit()
    db.refresh(plan)
    return plan


@router.get("", response_model=list[MealPlanPublic])
def list_plans(db: DbSession, current_user: CurrentUser) -> list[MealPlan]:
    return (
        db.query(MealPlan)
        .filter(MealPlan.owner_id == current_user.id)
        .order_by(MealPlan.created_at.desc())
        .all()
    )


@router.get("/{plan_id}", response_model=MealPlanPublic)
def get_plan(plan_id: int, db: DbSession, current_user: CurrentUser) -> MealPlan:
    return _get_owned(db, plan_id, current_user.id)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_plan(plan_id: int, db: DbSession, current_user: CurrentUser) -> None:
    plan = _get_owned(db, plan_id, current_user.id)
    db.delete(plan)
    db.commit()
