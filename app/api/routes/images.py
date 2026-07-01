"""Image upload / camera capture + ingredient detection routes (FR03-FR05)."""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.core.ids import next_id
from app.models.ingredient import Ingredient
from app.services.detection import detect_ingredients

router = APIRouter(prefix="/images", tags=["images"])

_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


async def _read_and_validate(file: UploadFile) -> bytes:
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type: {file.content_type}",
        )
    data = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.MAX_UPLOAD_MB} MB limit.",
        )
    return data


def _persist(data: bytes, suffix: str) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{suffix or '.img'}"
    path = os.path.join(settings.UPLOAD_DIR, fname)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


@router.post("/detect")
async def detect(
    current_user: CurrentUser,
    file: UploadFile = File(..., description="Gallery upload (FR03) or camera capture (FR04)."),
    max_results: int = Query(default=5, ge=1, le=20),
) -> dict:
    """Run ingredient detection on an uploaded/captured image (FR05).

    Returns detected ingredients without persisting them. Use ``/images/detect-and-save``
    to also add them to the user's inventory.
    """
    data = await _read_and_validate(file)
    detections = detect_ingredients(data, max_results=max_results)
    return {
        "filename": file.filename,
        "detections": [{"name": d.name, "confidence": d.confidence} for d in detections],
    }


@router.post("/detect-and-save", status_code=status.HTTP_201_CREATED)
async def detect_and_save(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    source: str = Query(default="image_upload", pattern="^(image_upload|camera)$"),
    expiry_date: str | None = Query(
        default=None, description="Optional DD/MM/YYYY future date applied to all items."
    ),
    max_results: int = Query(default=5, ge=1, le=20),
) -> dict:
    """Detect ingredients and add high-confidence ones to inventory (FR03-FR05, FR09)."""
    from app.schemas.validators import parse_future_date

    data = await _read_and_validate(file)
    _persist(data, os.path.splitext(file.filename or "")[1])

    parsed_expiry = None
    if expiry_date:
        parsed_expiry = parse_future_date(expiry_date)

    detections = detect_ingredients(data, max_results=max_results)
    created: list[dict] = []
    for d in detections:
        # expiry_date is mandatory for inventory items; without one we report the
        # detection but do not persist it (the client can confirm + set a date later).
        if parsed_expiry is None:
            created.append({"name": d.name, "confidence": d.confidence, "saved": False})
            continue
        ing = Ingredient(
            id=next_id(db, "ING", 3),
            owner_id=current_user.id,
            name=d.name,
            quantity=1.0,
            expiry_date=parsed_expiry,
            source=source,
        )
        db.add(ing)
        created.append({"id": ing.id, "name": d.name, "confidence": d.confidence, "saved": True})
    db.commit()
    return {"filename": file.filename, "source": source, "items": created}
