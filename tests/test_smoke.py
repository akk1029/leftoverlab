"""Smoke tests covering auth, validation rules, and core flows."""
from __future__ import annotations

from datetime import date, timedelta


def _future(days: int = 30) -> str:
    return (date.today() + timedelta(days=days)).strftime("%d/%m/%Y")


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_assigns_prefixed_id(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "a@example.com", "password": "Valid1!pass"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["id"].startswith("U") and len(body["id"]) == 4
    assert "hashed_password" not in body


def test_weak_password_rejected(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "b@example.com", "password": "weak"},
    )
    assert resp.status_code == 422


def test_invalid_dietary_preference_rejected(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "c@example.com", "password": "Valid1!pass", "dietary_preference": "Carnivore"},
    )
    assert resp.status_code == 422


def test_ingredient_validation_and_id(client, auth_headers):
    # Past date rejected
    bad = client.post(
        "/api/v1/ingredients",
        headers=auth_headers,
        json={"name": "Milk", "quantity": 1, "expiry_date": "01/01/2000"},
    )
    assert bad.status_code == 422

    # Zero quantity rejected
    bad2 = client.post(
        "/api/v1/ingredients",
        headers=auth_headers,
        json={"name": "Milk", "quantity": 0, "expiry_date": _future()},
    )
    assert bad2.status_code == 422

    ok = client.post(
        "/api/v1/ingredients",
        headers=auth_headers,
        json={"name": "Tomato", "quantity": 3, "expiry_date": _future()},
    )
    assert ok.status_code == 201, ok.text
    body = ok.json()
    assert body["id"].startswith("ING")
    assert body["expiry_date_display"] == _future()
    assert body["days_until_expiry"] >= 0


def test_recipe_recommendation_flow(client, auth_headers):
    client.post(
        "/api/v1/ingredients",
        headers=auth_headers,
        json={"name": "Tomato", "quantity": 2, "expiry_date": _future()},
    )
    client.post(
        "/api/v1/ingredients",
        headers=auth_headers,
        json={"name": "Garlic", "quantity": 1, "expiry_date": _future()},
    )
    client.post(
        "/api/v1/recipes",
        headers=auth_headers,
        json={
            "title": "Tomato Garlic Toast",
            "category": "Breakfast",
            "ingredients_text": "Tomato\nGarlic\nBread",
        },
    )
    recs = client.get("/api/v1/recipes/recommendations", headers=auth_headers)
    assert recs.status_code == 200
    data = recs.json()
    assert len(data) >= 1
    assert data[0]["match_score"] > 0
    assert "Bread" in [m.title() for m in data[0]["missing_ingredients"]]


def test_protected_route_requires_auth(client):
    assert client.get("/api/v1/ingredients").status_code == 401
