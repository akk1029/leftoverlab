"""TheMealDB integration — generate real recipes from a user's inventory.

Strategy (works with the free public API key "1"):
  1. For each inventory ingredient, call ``filter.php?i=<ingredient>`` to find
     meals that use it. Tally how many of the user's ingredients hit each meal.
  2. Look up full details (``lookup.php?i=<id>``) for the best-matching meals.
  3. Filter out meals that clash with the user's dietary preference or allergies
     (see ``app.services.dietary``).
  4. Score each surviving meal by the fraction of its ingredients the user owns,
     and return the best matches with matched/missing ingredient breakdowns.

All outbound calls are async and run concurrently (bounded by a semaphore) to
stay within the 5-second performance budget.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import httpx

from app.config import settings
from app.core.enums import DietaryPreference
from app.services.dietary import allergy_conflicts, dietary_conflict

# How many inventory items to query, how many candidates to fully look up,
# and how many concurrent requests to allow.
_MAX_FILTER_INGREDIENTS = 8
_MAX_CANDIDATES = 20
_CONCURRENCY = 6


@dataclass
class GeneratedMeal:
    id: str  # e.g. "themealdb:52772"
    mealdb_id: str
    title: str
    category: str | None
    area: str | None
    thumbnail: str | None
    source_url: str | None
    youtube_url: str | None
    instructions: str
    tags: list[str]
    ingredients: list[str]
    match_score: float = 0.0
    matched_ingredients: list[str] = field(default_factory=list)
    missing_ingredients: list[str] = field(default_factory=list)


def parse_meal(raw: dict) -> GeneratedMeal:
    """Normalize TheMealDB's flat strIngredient1..20 shape into a clean object."""
    ingredients: list[str] = []
    for i in range(1, 21):
        name = (raw.get(f"strIngredient{i}") or "").strip()
        if name:
            ingredients.append(name)
    tags = [t.strip() for t in (raw.get("strTags") or "").split(",") if t.strip()]
    return GeneratedMeal(
        id=f"themealdb:{raw.get('idMeal')}",
        mealdb_id=str(raw.get("idMeal")),
        title=raw.get("strMeal") or "Untitled",
        category=raw.get("strCategory"),
        area=raw.get("strArea"),
        thumbnail=raw.get("strMealThumb"),
        source_url=raw.get("strSource") or None,
        youtube_url=raw.get("strYoutube") or None,
        instructions=(raw.get("strInstructions") or "").strip(),
        tags=tags,
        ingredients=ingredients,
    )


async def _filter_by_ingredient(client: httpx.AsyncClient, name: str) -> list[dict]:
    try:
        r = await client.get("/filter.php", params={"i": name})
        r.raise_for_status()
        return r.json().get("meals") or []
    except (httpx.HTTPError, ValueError):
        return []


async def _lookup(client: httpx.AsyncClient, meal_id: str) -> GeneratedMeal | None:
    try:
        r = await client.get("/lookup.php", params={"i": meal_id})
        r.raise_for_status()
        meals = r.json().get("meals") or []
        return parse_meal(meals[0]) if meals else None
    except (httpx.HTTPError, ValueError, IndexError):
        return None


async def lookup_meal(meal_id: str) -> GeneratedMeal | None:
    """Public helper to fetch and parse a single meal by its TheMealDB id."""
    async with httpx.AsyncClient(base_url=settings.THEMEALDB_BASE_URL,
                                 timeout=settings.THEMEALDB_TIMEOUT) as client:
        return await _lookup(client, meal_id)


def _score(meal: GeneratedMeal, owned_lower: list[str]) -> None:
    """Populate match_score / matched / missing based on owned inventory."""
    matched, missing = [], []
    for ing in meal.ingredients:
        low = ing.lower()
        if any(o in low or low in o for o in owned_lower):
            matched.append(ing)
        else:
            missing.append(ing)
    meal.matched_ingredients = matched
    meal.missing_ingredients = missing
    meal.match_score = round(len(matched) / len(meal.ingredients), 2) if meal.ingredients else 0.0


async def generate_from_inventory(
    inventory_names: list[str],
    *,
    preference: DietaryPreference,
    allergies: list[str],
    limit: int = 10,
    respect_dietary: bool = True,
    respect_allergies: bool = True,
) -> list[GeneratedMeal]:
    """Return dietary/allergy-safe TheMealDB recipes ranked by inventory match."""
    if not inventory_names:
        return []

    owned_lower = [n.strip().lower() for n in inventory_names if n.strip()]
    query_names = inventory_names[:_MAX_FILTER_INGREDIENTS]
    sem = asyncio.Semaphore(_CONCURRENCY)

    async with httpx.AsyncClient(
        base_url=settings.THEMEALDB_BASE_URL, timeout=settings.THEMEALDB_TIMEOUT
    ) as client:
        async def filt(name: str) -> tuple[str, list[dict]]:
            async with sem:
                return name, await _filter_by_ingredient(client, name)

        filtered = await asyncio.gather(*(filt(n) for n in query_names))

        # Tally: meal id -> how many distinct inventory items matched it.
        tally: dict[str, int] = {}
        for _owned, meals in filtered:
            for m in meals:
                mid = str(m.get("idMeal"))
                tally[mid] = tally.get(mid, 0) + 1
        if not tally:
            return []

        # Look up the meals that matched the most inventory items.
        top_ids = [mid for mid, _ in sorted(tally.items(), key=lambda kv: kv[1], reverse=True)][:_MAX_CANDIDATES]

        async def look(mid: str) -> GeneratedMeal | None:
            async with sem:
                return await _lookup(client, mid)

        detailed = await asyncio.gather(*(look(mid) for mid in top_ids))

    results: list[GeneratedMeal] = []
    for meal in detailed:
        if meal is None or not meal.ingredients:
            continue
        if respect_dietary and dietary_conflict(meal.ingredients, preference):
            continue
        if respect_allergies and allergy_conflicts(meal.ingredients, allergies):
            continue
        _score(meal, owned_lower)
        results.append(meal)

    # Best inventory coverage first; break ties by fewest missing ingredients.
    results.sort(key=lambda m: (m.match_score, -len(m.missing_ingredients)), reverse=True)
    return results[:limit]
