"""Dietary-restriction and allergy filtering (pure, network-free, testable).

Given a list of ingredient names (from any recipe source, e.g. TheMealDB) these
helpers decide whether the recipe conflicts with a user's ``DietaryPreference``
or any of their declared allergies. Matching is done on whole words to avoid
false positives (e.g. "ham" must not match inside "graham cracker").
"""
from __future__ import annotations

import re

from app.core.enums import DietaryPreference

# --- keyword vocabularies (all lower-case, whole-word matched) ---------------

_MEAT_AND_FISH = {
    "beef", "chicken", "pork", "lamb", "bacon", "ham", "gammon", "sausage",
    "turkey", "duck", "veal", "venison", "goat", "mince", "meat", "meatball",
    "chorizo", "pepperoni", "prosciutto", "salami", "pastrami", "oxtail",
    "fish", "salmon", "tuna", "cod", "haddock", "anchovy", "anchovies",
    "sardine", "sardines", "mackerel", "kipper", "prawn", "prawns", "shrimp",
    "crab", "lobster", "clam", "clams", "mussel", "mussels", "oyster",
    "oysters", "scallop", "scallops", "squid", "octopus", "crayfish",
    "gelatin", "gelatine", "lard", "suet", "stock cube", "fish sauce",
}

# Vegan additionally excludes animal products.
_ANIMAL_PRODUCTS = {
    "milk", "cheese", "butter", "cream", "creme", "egg", "eggs", "honey",
    "yogurt", "yoghurt", "ghee", "mayonnaise", "mayo", "custard", "buttermilk",
    "parmesan", "mozzarella", "cheddar", "feta", "ricotta", "mascarpone",
    "condensed milk", "whey", "casein", "lard",
}

# Non-halal: pork products + alcohol.
_NON_HALAL = {
    "pork", "bacon", "ham", "gammon", "lard", "chorizo", "pepperoni",
    "prosciutto", "salami", "pancetta", "wine", "beer", "rum", "brandy",
    "vodka", "whisky", "whiskey", "bourbon", "sherry", "liqueur", "sake",
    "mirin", "cooking wine", "rice wine", "marsala", "alcohol", "gelatin",
    "gelatine",
}

_GLUTEN = {
    "wheat", "flour", "bread", "breadcrumb", "breadcrumbs", "panko", "pasta",
    "spaghetti", "macaroni", "noodle", "noodles", "barley", "rye", "couscous",
    "semolina", "cracker", "crackers", "biscuit", "biscuits", "cake", "pastry",
    "soy sauce", "beer", "bulgur", "farro", "seitan", "tortilla", "pita",
    "naan", "roux", "lasagne", "lasagna", "dumpling", "filo", "phyllo",
    "puff pastry", "self-raising flour", "plain flour",
}

# Expand common allergy terms into concrete ingredient keywords.
_ALLERGY_EXPANSIONS: dict[str, set[str]] = {
    "shellfish": {"shrimp", "prawn", "prawns", "crab", "lobster", "clam", "clams",
                  "mussel", "mussels", "oyster", "oysters", "scallop", "scallops",
                  "squid", "crayfish"},
    "nuts": {"almond", "almonds", "walnut", "walnuts", "cashew", "cashews",
             "pecan", "pecans", "pistachio", "pistachios", "hazelnut",
             "hazelnuts", "macadamia", "brazil nut", "pine nut", "nuts"},
    "tree nuts": {"almond", "walnut", "cashew", "pecan", "pistachio",
                  "hazelnut", "macadamia", "brazil nut"},
    "peanut": {"peanut", "peanuts", "groundnut", "groundnuts"},
    "peanuts": {"peanut", "peanuts", "groundnut", "groundnuts"},
    "dairy": {"milk", "cheese", "butter", "cream", "yogurt", "yoghurt", "ghee",
              "buttermilk", "whey", "casein", "parmesan", "cheddar", "mozzarella"},
    "milk": {"milk", "cheese", "butter", "cream", "yogurt", "yoghurt", "ghee",
             "buttermilk"},
    "lactose": {"milk", "cheese", "butter", "cream", "yogurt", "yoghurt"},
    "egg": {"egg", "eggs", "mayonnaise", "mayo"},
    "eggs": {"egg", "eggs", "mayonnaise", "mayo"},
    "gluten": _GLUTEN,
    "wheat": {"wheat", "flour", "bread", "pasta", "couscous", "semolina"},
    "soy": {"soy", "soya", "tofu", "edamame", "soy sauce", "miso", "tempeh"},
    "soya": {"soy", "soya", "tofu", "edamame", "soy sauce", "miso", "tempeh"},
    "fish": {"fish", "salmon", "tuna", "cod", "haddock", "anchovy", "anchovies",
             "sardine", "sardines", "mackerel"},
    "sesame": {"sesame", "tahini"},
    "mustard": {"mustard"},
    "celery": {"celery", "celeriac"},
}

_DIETARY_KEYWORDS: dict[DietaryPreference, set[str]] = {
    DietaryPreference.VEGETARIAN: _MEAT_AND_FISH,
    DietaryPreference.VEGAN: _MEAT_AND_FISH | _ANIMAL_PRODUCTS,
    DietaryPreference.HALAL: _NON_HALAL,
    DietaryPreference.GLUTEN_FREE: _GLUTEN,
}


def _word_hit(text: str, keyword: str) -> bool:
    """True if ``keyword`` appears as a whole word/phrase inside ``text``."""
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def _first_conflict(ingredient_names: list[str], keywords: set[str]) -> str | None:
    for name in ingredient_names:
        low = name.lower()
        for kw in keywords:
            if _word_hit(low, kw):
                return name
    return None


def dietary_conflict(ingredient_names: list[str], preference: DietaryPreference) -> str | None:
    """Return the offending ingredient if the recipe violates ``preference``, else None."""
    if preference == DietaryPreference.NONE:
        return None
    keywords = _DIETARY_KEYWORDS.get(preference)
    if not keywords:
        return None
    return _first_conflict(ingredient_names, keywords)


def parse_allergies(raw: str | None) -> list[str]:
    """Split a stored comma-separated allergy string into normalized terms."""
    if not raw:
        return []
    return [a.strip().lower() for a in raw.split(",") if a.strip()]


def allergy_conflicts(ingredient_names: list[str], allergies: list[str]) -> list[str]:
    """Return the list of recipe ingredients that clash with any declared allergy."""
    if not allergies:
        return []
    # Build the full keyword set: each allergy term plus its expansions.
    keywords: set[str] = set()
    for term in allergies:
        keywords.add(term)
        keywords |= _ALLERGY_EXPANSIONS.get(term, set())

    hits: list[str] = []
    for name in ingredient_names:
        low = name.lower()
        if any(_word_hit(low, kw) for kw in keywords):
            hits.append(name)
    return hits
