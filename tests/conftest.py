"""Pytest fixtures: spin up the app against an isolated SQLite database."""
from __future__ import annotations

import os

# Point the app at a throwaway SQLite DB BEFORE importing app modules.
os.environ["DATABASE_URL"] = "sqlite:///./test_leftoverlab.db"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.database as database  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _sqlite_engine():
    # Use a shared in-memory SQLite DB across the test session.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.engine = engine
    database.SessionLocal.configure(bind=engine)
    yield engine


@pytest.fixture()
def client(_sqlite_engine):
    from app.database import Base
    import app.models  # noqa: F401  (register tables)

    Base.metadata.drop_all(bind=_sqlite_engine)
    Base.metadata.create_all(bind=_sqlite_engine)

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    """Register + log in a user, returning Authorization headers."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "cook@example.com", "password": "Sup3r!pass", "full_name": "Cook"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "cook@example.com", "password": "Sup3r!pass"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
