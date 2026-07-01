"""Voice-controlled kitchen mode (FR15).

The actual speech-to-text happens on the device. This endpoint takes the
transcribed text and resolves it into a structured intent the client can act on
(navigate steps, repeat, set a timer, read ingredients).
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.models.recipe import Recipe

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceCommand(BaseModel):
    transcript: str = Field(..., min_length=1)
    recipe_id: str | None = Field(default=None, description="Recipe currently being cooked.")
    current_step: int = Field(default=0, ge=0)


class VoiceResponse(BaseModel):
    intent: str
    say: str
    data: dict = Field(default_factory=dict)


_TIMER_RE = re.compile(r"(\d+)\s*(second|seconds|minute|minutes|hour|hours)")


def _steps(recipe: Recipe) -> list[str]:
    return [s.strip() for s in re.split(r"[\n]+|\d+\.\s", recipe.instructions or "") if s.strip()]


@router.post("/command", response_model=VoiceResponse)
def handle_command(
    payload: VoiceCommand, db: DbSession, current_user: CurrentUser
) -> VoiceResponse:
    text = payload.transcript.lower().strip()

    recipe = db.get(Recipe, payload.recipe_id) if payload.recipe_id else None
    steps = _steps(recipe) if recipe else []

    # --- Timer ---
    m = _TIMER_RE.search(text)
    if "timer" in text or "set a timer" in text or (m and "timer" in text):
        if m:
            value, unit = int(m.group(1)), m.group(2)
            seconds = value * {"second": 1, "seconds": 1, "minute": 60, "minutes": 60, "hour": 3600, "hours": 3600}[unit]
            return VoiceResponse(
                intent="set_timer",
                say=f"Timer set for {value} {unit}.",
                data={"seconds": seconds},
            )
        return VoiceResponse(intent="set_timer", say="How long should I set the timer for?")

    # --- Navigation ---
    if any(k in text for k in ("next", "next step")):
        nxt = min(payload.current_step + 1, max(len(steps) - 1, 0))
        return VoiceResponse(
            intent="next_step",
            say=steps[nxt] if steps else "No recipe loaded.",
            data={"step": nxt},
        )
    if any(k in text for k in ("previous", "go back", "back")):
        prev = max(payload.current_step - 1, 0)
        return VoiceResponse(
            intent="previous_step",
            say=steps[prev] if steps else "No recipe loaded.",
            data={"step": prev},
        )
    if "repeat" in text or "say again" in text:
        cur = payload.current_step if steps else 0
        return VoiceResponse(
            intent="repeat_step",
            say=steps[cur] if steps else "No recipe loaded.",
            data={"step": cur},
        )
    if "ingredient" in text:
        if recipe is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No recipe loaded."
            )
        return VoiceResponse(
            intent="read_ingredients",
            say=recipe.ingredients_text or "No ingredients listed.",
            data={"ingredients_text": recipe.ingredients_text},
        )

    return VoiceResponse(
        intent="unknown",
        say="Sorry, I didn't catch that. Try 'next step', 'repeat', or 'set a timer for 5 minutes'.",
    )
