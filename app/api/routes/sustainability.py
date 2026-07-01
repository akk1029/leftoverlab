"""Sustainability dashboard routes (FR13)."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func

from app.api.deps import CurrentUser, DbSession
from app.models.sustainability import SustainabilityRecord
from app.schemas.sustainability import (
    SustainabilityDashboard,
    SustainabilityRecordCreate,
    SustainabilityRecordPublic,
)

router = APIRouter(prefix="/sustainability", tags=["sustainability"])


def _achievements(money: float, carbon: float, food: float, count: int) -> list[str]:
    earned: list[str] = []
    if count >= 1:
        earned.append("First Save 🌱")
    if count >= 10:
        earned.append("Waste Warrior ♻️")
    if money >= 100:
        earned.append("Money Saver 💰")
    if carbon >= 50:
        earned.append("Carbon Cutter 🌍")
    if food >= 25:
        earned.append("Food Rescuer 🥗")
    return earned


@router.post("/records", response_model=SustainabilityRecordPublic, status_code=201)
def add_record(
    payload: SustainabilityRecordCreate, db: DbSession, current_user: CurrentUser
) -> SustainabilityRecord:
    record = SustainabilityRecord(owner_id=current_user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/records", response_model=list[SustainabilityRecordPublic])
def list_records(db: DbSession, current_user: CurrentUser) -> list[SustainabilityRecord]:
    return (
        db.query(SustainabilityRecord)
        .filter(SustainabilityRecord.owner_id == current_user.id)
        .order_by(SustainabilityRecord.created_at.desc())
        .all()
    )


@router.get("/dashboard", response_model=SustainabilityDashboard)
def dashboard(db: DbSession, current_user: CurrentUser) -> SustainabilityDashboard:
    row = (
        db.query(
            func.coalesce(func.sum(SustainabilityRecord.money_saved), 0.0),
            func.coalesce(func.sum(SustainabilityRecord.carbon_reduction_kg), 0.0),
            func.coalesce(func.sum(SustainabilityRecord.food_saved_kg), 0.0),
            func.count(SustainabilityRecord.id),
        )
        .filter(SustainabilityRecord.owner_id == current_user.id)
        .one()
    )
    money, carbon, food, count = float(row[0]), float(row[1]), float(row[2]), int(row[3])
    return SustainabilityDashboard(
        total_money_saved=round(money, 2),
        total_carbon_reduction_kg=round(carbon, 2),
        total_food_saved_kg=round(food, 2),
        records_count=count,
        achievements=_achievements(money, carbon, food, count),
    )
