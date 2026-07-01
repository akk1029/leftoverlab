"""Aggregate all v1 routers under a single APIRouter."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    auth,
    community,
    images,
    ingredients,
    mealplan,
    recipes,
    shopping,
    sustainability,
    users,
    voice,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(ingredients.router)
api_router.include_router(images.router)
api_router.include_router(recipes.router)
api_router.include_router(shopping.router)
api_router.include_router(mealplan.router)
api_router.include_router(sustainability.router)
api_router.include_router(community.router)
api_router.include_router(voice.router)
