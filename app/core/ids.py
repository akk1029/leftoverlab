"""Human-readable prefixed primary keys (e.g. U001, ING001, REC001, P0001).

The data rules require sequential business identifiers per entity. We keep a
dedicated ``id_counters`` table so generation is atomic and gap-free even under
concurrent inserts: each call locks the counter row, increments it, and formats
the value with the entity's prefix and zero-padded width.
"""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database import Base


class IdCounter(Base):
    __tablename__ = "id_counters"

    prefix: Mapped[str] = mapped_column(String(8), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


def next_id(db: Session, prefix: str, width: int) -> str:
    """Atomically produce the next id for ``prefix`` (e.g. ('U', 3) -> 'U001').

    Uses ``SELECT ... FOR UPDATE`` to serialize concurrent generation.
    The caller is responsible for committing the surrounding transaction.
    """
    counter = (
        db.query(IdCounter)
        .filter(IdCounter.prefix == prefix)
        .with_for_update()
        .one_or_none()
    )
    if counter is None:
        counter = IdCounter(prefix=prefix, value=0)
        db.add(counter)
        db.flush()
        counter = (
            db.query(IdCounter)
            .filter(IdCounter.prefix == prefix)
            .with_for_update()
            .one()
        )

    counter.value += 1
    db.flush()
    return f"{prefix}{counter.value:0{width}d}"
