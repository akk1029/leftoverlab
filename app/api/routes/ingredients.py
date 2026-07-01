"""Ingredient inventory + expiry tracking routes (FR09, FR10)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.core.ids import next_id
from app.models.ingredient import Ingredient
from app.schemas.ingredient import (
    IngredientCreate,
    IngredientPublic,
    IngredientUpdate,
)
from app.services.storage_guidance import get_guidance

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


def _get_owned(db: DbSession, ingredient_id: str, owner_id: str) -> Ingredient:
    ing = db.get(Ingredient, ingredient_id)
    if ing is None or ing.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found.")
    return ing


@router.post("", response_model=IngredientPublic, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    payload: IngredientCreate, db: DbSession, current_user: CurrentUser
) -> Ingredient:
    ing = Ingredient(
        id=next_id(db, "ING", 3),
        owner_id=current_user.id,
        name=payload.name,
        quantity=payload.quantity,
        unit=payload.unit,
        expiry_date=payload.expiry_date,  # already a date after validation
        storage_location=payload.storage_location,
        source="manual",
    )
    db.add(ing)
    db.commit()
    db.refresh(ing)
    return ing


@router.get("", response_model=list[IngredientPublic])
def list_ingredients(db: DbSession, current_user: CurrentUser) -> list[Ingredient]:
    return (
        db.query(Ingredient)
        .filter(Ingredient.owner_id == current_user.id)
        .order_by(Ingredient.expiry_date.asc())
        .all()
    )


@router.get("/expiring", response_model=list[IngredientPublic])
def list_expiring(
    db: DbSession,
    current_user: CurrentUser,
    within_days: int = Query(default=3, ge=0, le=365),
) -> list[Ingredient]:
    """Smart Expiry Tracker: ingredients expiring within N days (FR09)."""
    cutoff = date.today() + timedelta(days=within_days)
    return (
        db.query(Ingredient)
        .filter(
            Ingredient.owner_id == current_user.id,
            Ingredient.expiry_date <= cutoff,
        )
        .order_by(Ingredient.expiry_date.asc())
        .all()
    )


@router.get("/{ingredient_id}", response_model=IngredientPublic)
def get_ingredient(
    ingredient_id: str, db: DbSession, current_user: CurrentUser
) -> Ingredient:
    return _get_owned(db, ingredient_id, current_user.id)


@router.patch("/{ingredient_id}", response_model=IngredientPublic)
def update_ingredient(
    ingredient_id: str,
    payload: IngredientUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Ingredient:
    ing = _get_owned(db, ingredient_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(ing, field, value)
    db.add(ing)
    db.commit()
    db.refresh(ing)
    return ing


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_ingredient(
    ingredient_id: str, db: DbSession, current_user: CurrentUser
) -> None:
    ing = _get_owned(db, ingredient_id, current_user.id)
    db.delete(ing)
    db.commit()


@router.get("/{ingredient_id}/storage-guidance")
def storage_guidance(
    ingredient_id: str, db: DbSession, current_user: CurrentUser
) -> dict:
    """Storage Guidance System for a stored ingredient (FR10)."""
    ing = _get_owned(db, ingredient_id, current_user.id)
    g = get_guidance(ing.name)
    return {
        "ingredient": g.ingredient,
        "storage": g.storage,
        "fridge_days": g.fridge_days,
        "freezer_days": g.freezer_days,
        "reheating": g.reheating,
        "safety_tips": g.safety_tips,
    }
