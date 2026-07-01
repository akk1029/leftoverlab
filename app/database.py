"""SQLAlchemy engine, session factory, and declarative base."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # avoid stale connections (important on Render free tier)
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Arbitrary constant key identifying the "schema init" advisory lock.
_SCHEMA_LOCK_KEY = 727214


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables, safe to call from multiple workers concurrently.

    Running Gunicorn with several workers means each one executes the startup
    hook, so a naive ``create_all`` races: two workers both see a table as
    missing and both issue ``CREATE TABLE``, and the loser crashes with a
    duplicate-key error on ``pg_type``. On PostgreSQL we take a transaction-level
    advisory lock so exactly one worker builds the schema while the others wait
    and then find the tables already present. SQLite (local/tests) needs no lock.
    """
    # Import here so all models are registered on Base.metadata before create_all.
    import app.models  # noqa: F401

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _SCHEMA_LOCK_KEY})
            Base.metadata.create_all(bind=conn)
    else:
        Base.metadata.create_all(bind=engine)
