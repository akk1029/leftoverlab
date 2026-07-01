"""User profile management routes (FR02)."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas.user import UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def get_profile(current_user: CurrentUser) -> User:
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_profile(
    payload: UserUpdate, db: DbSession, current_user: CurrentUser
) -> User:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
