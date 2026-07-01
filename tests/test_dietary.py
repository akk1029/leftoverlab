"""Unit tests for dietary-restriction and allergy filtering (no network)."""
from __future__ import annotations

from app.core.enums import DietaryPreference
from app.services.dietary import (
    allergy_conflicts,
    dietary_conflict,
    parse_allergies,
)


def test_vegetarian_rejects_meat_and_fish():
    assert dietary_conflict(["Tomato", "Chicken breast"], DietaryPreference.VEGETARIAN) == "Chicken breast"
    assert dietary_conflict(["Tomato", "Salmon"], DietaryPreference.VEGETARIAN) == "Salmon"
    assert dietary_conflict(["Tomato", "Onion", "Rice"], DietaryPreference.VEGETARIAN) is None


def test_vegan_rejects_dairy_and_eggs():
    assert dietary_conflict(["Spinach", "Cheese"], DietaryPreference.VEGAN) == "Cheese"
    assert dietary_conflict(["Flour", "Egg"], DietaryPreference.VEGAN) == "Egg"
    assert dietary_conflict(["Tomato", "Chickpeas"], DietaryPreference.VEGAN) is None


def test_halal_rejects_pork_and_alcohol():
    assert dietary_conflict(["Bacon", "Egg"], DietaryPreference.HALAL) == "Bacon"
    assert dietary_conflict(["Beef", "Red wine"], DietaryPreference.HALAL) == "Red wine"
    # Halal allows beef/chicken with no pork/alcohol.
    assert dietary_conflict(["Beef", "Onion"], DietaryPreference.HALAL) is None


def test_gluten_free_rejects_wheat():
    assert dietary_conflict(["Plain flour", "Egg"], DietaryPreference.GLUTEN_FREE) == "Plain flour"
    assert dietary_conflict(["Spaghetti", "Tomato"], DietaryPreference.GLUTEN_FREE) == "Spaghetti"
    assert dietary_conflict(["Rice", "Chicken"], DietaryPreference.GLUTEN_FREE) is None


def test_none_preference_allows_everything():
    assert dietary_conflict(["Pork", "Wine", "Flour"], DietaryPreference.NONE) is None


def test_whole_word_matching_avoids_false_positives():
    # "ham" must not match inside "graham cracker".
    assert dietary_conflict(["Graham cracker"], DietaryPreference.HALAL) is None


def test_allergy_expansion():
    allergies = parse_allergies("shellfish, peanuts")
    assert allergy_conflicts(["Prawns", "Garlic"], allergies) == ["Prawns"]
    assert allergy_conflicts(["Peanut butter"], allergies) == ["Peanut butter"]
    assert allergy_conflicts(["Chicken", "Rice"], allergies) == []


def test_parse_allergies_empty():
    assert parse_allergies(None) == []
    assert parse_allergies("  ") == []
    assert parse_allergies("Nuts, ,Dairy") == ["nuts", "dairy"]
