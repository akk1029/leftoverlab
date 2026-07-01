"""Ingredient detection service (FR05).

This is a *pluggable stub*. A real deployment would replace ``detect_ingredients``
with a call to a vision model (e.g. a hosted classifier, AWS Rekognition, a custom
PyTorch/TF model, or a multimodal LLM). The rest of the app only depends on the
return shape, so swapping the implementation requires no other changes.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

# A small built-in vocabulary the stub can "recognise".
_VOCAB = [
    "Tomato", "Onion", "Garlic", "Egg", "Milk", "Cheese", "Chicken",
    "Carrot", "Potato", "Spinach", "Bell Pepper", "Rice", "Pasta",
    "Apple", "Banana", "Lettuce", "Cucumber", "Mushroom", "Broccoli", "Yogurt",
]


@dataclass
class DetectedIngredient:
    name: str
    confidence: float


def detect_ingredients(image_bytes: bytes, max_results: int = 5) -> list[DetectedIngredient]:
    """Return a deterministic, fake set of detections for the given image.

    Deterministic so the same image yields the same result in demos/tests.
    Replace the body with a real model call in production.
    """
    if not image_bytes:
        return []

    digest = hashlib.sha256(image_bytes).digest()
    results: list[DetectedIngredient] = []
    seen: set[str] = set()
    for i, byte in enumerate(digest):
        if len(results) >= max_results:
            break
        name = _VOCAB[byte % len(_VOCAB)]
        if name in seen:
            continue
        seen.add(name)
        # Map a byte to a plausible confidence in [0.55, 0.99].
        confidence = round(0.55 + (digest[(i + 7) % len(digest)] / 255) * 0.44, 2)
        results.append(DetectedIngredient(name=name, confidence=confidence))
    return results
