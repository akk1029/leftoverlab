"""Food storage / safety guidance service (FR10).

A simple knowledge base keyed by ingredient name (case-insensitive substring
match), with a sensible default. Easily extended or swapped for a DB-backed table.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StorageGuidance:
    ingredient: str
    storage: str
    fridge_days: int | None = None
    freezer_days: int | None = None
    reheating: str | None = None
    safety_tips: list[str] = field(default_factory=list)


_GUIDANCE: dict[str, StorageGuidance] = {
    "chicken": StorageGuidance(
        ingredient="Chicken",
        storage="Refrigerate at or below 4°C in a sealed container.",
        fridge_days=2,
        freezer_days=270,
        reheating="Reheat to an internal temperature of 74°C.",
        safety_tips=["Never refreeze thawed raw chicken.", "Keep separate from ready-to-eat foods."],
    ),
    "milk": StorageGuidance(
        ingredient="Milk",
        storage="Keep refrigerated; store on a shelf, not the door.",
        fridge_days=7,
        freezer_days=90,
        reheating="Warm gently; do not boil repeatedly.",
        safety_tips=["Discard if sour-smelling or curdled."],
    ),
    "egg": StorageGuidance(
        ingredient="Egg",
        storage="Refrigerate in the original carton.",
        fridge_days=28,
        freezer_days=365,
        reheating="Cook until both yolk and white are firm.",
        safety_tips=["Discard cracked eggs.", "Float test: bad eggs float in water."],
    ),
    "spinach": StorageGuidance(
        ingredient="Spinach",
        storage="Refrigerate unwashed in a breathable bag.",
        fridge_days=5,
        freezer_days=300,
        reheating="Use within a day once cooked.",
        safety_tips=["Wash thoroughly before use."],
    ),
}

_DEFAULT = StorageGuidance(
    ingredient="Generic",
    storage="Store in a cool, dry place or refrigerate perishables promptly.",
    fridge_days=5,
    freezer_days=180,
    reheating="Reheat thoroughly until steaming hot.",
    safety_tips=["When in doubt, throw it out."],
)


def get_guidance(ingredient_name: str) -> StorageGuidance:
    key = ingredient_name.strip().lower()
    for known, guidance in _GUIDANCE.items():
        if known in key:
            return guidance
    return StorageGuidance(
        ingredient=ingredient_name,
        storage=_DEFAULT.storage,
        fridge_days=_DEFAULT.fridge_days,
        freezer_days=_DEFAULT.freezer_days,
        reheating=_DEFAULT.reheating,
        safety_tips=list(_DEFAULT.safety_tips),
    )
