"""Shopping list routes, incl. auto-generation from recipes (FR11)."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.ids import next_id
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe
from app.models.shopping import ShoppingList, ShoppingListItem
from app.schemas.shopping import (
    GenerateFromRecipesRequest,
    ShoppingListCreate,
    ShoppingListItemCreate,
    ShoppingListItemPublic,
    ShoppingListItemUpdate,
    ShoppingListPublic,
)

router = APIRouter(prefix="/shopping-lists", tags=["shopping"])


def _get_owned(db: DbSession, list_id: str, owner_id: str) -> ShoppingList:
    sl = db.get(ShoppingList, list_id)
    if sl is None or sl.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found.")
    return sl


def _tokenize(text: str) -> list[str]:
    parts = re.split(r"[,\n;]+", text or "")
    return [p.strip() for p in parts if p.strip()]


@router.post("", response_model=ShoppingListPublic, status_code=status.HTTP_201_CREATED)
def create_list(
    payload: ShoppingListCreate, db: DbSession, current_user: CurrentUser
) -> ShoppingList:
    sl = ShoppingList(id=next_id(db, "SL", 3), owner_id=current_user.id, name=payload.name)
    sl.items = [
        ShoppingListItem(name=i.name, quantity=i.quantity, unit=i.unit)
        for i in payload.items
    ]
    db.add(sl)
    db.commit()
    db.refresh(sl)
    return sl


@router.post("/generate", response_model=ShoppingListPublic, status_code=status.HTTP_201_CREATED)
def generate_from_recipes(
    payload: GenerateFromRecipesRequest, db: DbSession, current_user: CurrentUser
) -> ShoppingList:
    """Shopping List Generation from selected recipes (FR11)."""
    recipes = db.query(Recipe).filter(Recipe.id.in_(payload.recipe_ids)).all()
    if not recipes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching recipes.")

    owned: set[str] = set()
    if payload.exclude_owned:
        owned = {
            i.name.strip().lower()
            for i in db.query(Ingredient).filter(Ingredient.owner_id == current_user.id).all()
        }

    needed: dict[str, str] = {}  # lower -> original casing
    for recipe in recipes:
        for token in _tokenize(recipe.ingredients_text):
            key = token.lower()
            if key in owned:
                continue
            needed.setdefault(key, token)

    sl = ShoppingList(id=next_id(db, "SL", 3), owner_id=current_user.id, name=payload.name)
    sl.items = [ShoppingListItem(name=name, quantity=1.0) for name in needed.values()]
    db.add(sl)
    db.commit()
    db.refresh(sl)
    return sl


@router.get("", response_model=list[ShoppingListPublic])
def list_lists(db: DbSession, current_user: CurrentUser) -> list[ShoppingList]:
    return (
        db.query(ShoppingList)
        .filter(ShoppingList.owner_id == current_user.id)
        .order_by(ShoppingList.created_at.desc())
        .all()
    )


@router.get("/{list_id}", response_model=ShoppingListPublic)
def get_list(list_id: str, db: DbSession, current_user: CurrentUser) -> ShoppingList:
    return _get_owned(db, list_id, current_user.id)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_list(list_id: str, db: DbSession, current_user: CurrentUser) -> None:
    sl = _get_owned(db, list_id, current_user.id)
    db.delete(sl)
    db.commit()


@router.post("/{list_id}/items", response_model=ShoppingListItemPublic, status_code=status.HTTP_201_CREATED)
def add_item(
    list_id: str,
    payload: ShoppingListItemCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ShoppingListItem:
    sl = _get_owned(db, list_id, current_user.id)
    item = ShoppingListItem(
        shopping_list_id=sl.id, name=payload.name, quantity=payload.quantity, unit=payload.unit
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{list_id}/items/{item_id}", response_model=ShoppingListItemPublic)
def update_item(
    list_id: str,
    item_id: int,
    payload: ShoppingListItemUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ShoppingListItem:
    sl = _get_owned(db, list_id, current_user.id)
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.shopping_list_id != sl.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_item(
    list_id: str, item_id: int, db: DbSession, current_user: CurrentUser
) -> None:
    sl = _get_owned(db, list_id, current_user.id)
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.shopping_list_id != sl.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    db.delete(item)
    db.commit()
