# LeftoverLab — AI-Powered Smart Kitchen & Meal Planner (Backend API)

A FastAPI + PostgreSQL backend implementing the Smart Kitchen & Meal Planner
specification (FR01–FR15). It exposes a JSON REST API consumed by the mobile
(Android/iOS) client, and is configured for one-click deployment on
[Render](https://render.com).

> The mobile app (camera capture UI, on-device speech-to-text, push
> notifications) is a separate frontend project. This repo is the server: it
> handles data, auth, validation, ingredient detection, recommendations, and all
> business logic.

---

## Features → Requirements map

| Requirement | Where |
| :-- | :-- |
| FR01 Registration & Login (JWT) | `app/api/routes/auth.py` |
| FR02 Profile management | `app/api/routes/users.py` |
| FR03/FR04 Image upload & camera capture | `app/api/routes/images.py` |
| FR05 Ingredient detection (pluggable) | `app/services/detection.py` |
| FR06 Personalized recommendations | `app/api/routes/recipes.py` (`/recommendations`) |
| FR07 Recipe filtering | `app/api/routes/recipes.py` (`GET /recipes`) |
| FR08 Save & manage recipes | `app/api/routes/recipes.py` (`/save`, `/saved`) |
| FR09 Smart expiry tracker | `app/api/routes/ingredients.py` (`/expiring`) |
| FR10 Storage guidance | `app/services/storage_guidance.py` |
| FR11 Shopping list generation | `app/api/routes/shopping.py` (`/generate`) |
| FR12 Smart meal planner | `app/api/routes/mealplan.py` (`/generate`) |
| FR13 Sustainability dashboard | `app/api/routes/sustainability.py` |
| FR14 Community platform | `app/api/routes/community.py` |
| FR15 Voice-controlled kitchen mode | `app/api/routes/voice.py` |

All data-validation rules from section 2 (prefixed IDs, password policy,
dietary/category enums, future expiry dates, positive quantities) are enforced
in `app/schemas/` and `app/core/`.

---

## Tech stack

- **FastAPI** (async web framework) + **Pydantic v2** (validation)
- **SQLAlchemy 2.0** ORM + **PostgreSQL** (via `psycopg2`)
- **JWT** auth (`python-jose`) with **bcrypt** password hashing (`passlib`)
- **Gunicorn + Uvicorn workers** in production
- **pytest** smoke tests

---

## Project layout

```
app/
  main.py            # FastAPI app factory + lifespan (auto-creates tables)
  config.py          # env-driven settings
  database.py        # engine, session, declarative Base
  core/
    enums.py         # DietaryPreference, RecipeCategory
    security.py      # hashing + JWT
    ids.py           # atomic prefixed-id generator (U001, ING001, ...)
  models/            # SQLAlchemy ORM models
  schemas/           # Pydantic request/response models + validators
  services/
    detection.py     # ingredient recognition stub (swap for a real model)
    storage_guidance.py
  api/
    deps.py          # DB session + current-user dependencies
    api.py           # router aggregation
    routes/          # one module per feature area
scripts/seed.py      # seed sample recipes
tests/               # pytest smoke tests (SQLite)
render.yaml          # Render Blueprint (web service + Postgres)
Dockerfile           # optional container build
```

---

## Run locally

### 1. Prerequisites
- Python 3.11+ (3.12 recommended)
- Note: Open docker app before running the following command
- A local PostgreSQL instance (or use Docker: `docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16`)

### 2. Setup
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env        # then edit DATABASE_URL + SECRET_KEY
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3. Seed sample recipes (optional)
```bash
python -m scripts.seed
```

### 4. Start the server
```bash
uvicorn app.main:app --reload
```

Open the interactive docs at **http://localhost:8000/docs**.

### 5. Run tests
```bash
pip install -r requirements-dev.txt
pytest
```
Tests run against an isolated in-memory SQLite database — no Postgres needed.

---

## Deploy to Render

This repo includes a **`render.yaml` Blueprint** that provisions both the web
service and a managed PostgreSQL database, wiring `DATABASE_URL` automatically.

1. Push this repository to GitHub.
2. In the Render dashboard: **New + → Blueprint**, select your repo.
3. Render reads `render.yaml`, creates `leftoverlab-db` (Postgres) and
   `leftoverlab-api` (web service), and injects `DATABASE_URL` + a generated
   `SECRET_KEY`.
4. Click **Apply**. First deploy runs:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker ...`
   - Tables are auto-created on startup; health check hits `/health`.
5. Visit `https://<your-service>.onrender.com/docs`.

> **Free tier note:** the free web service sleeps after inactivity and the free
> Postgres database expires after ~90 days. Upgrade plans in `render.yaml` for
> production. To seed recipes on Render, open a **Shell** on the service and run
> `python -m scripts.seed`.

### Manual deploy (without Blueprint)
Create a **Web Service** from the repo and set:
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
- Add a PostgreSQL instance and copy its **Internal Connection String** into a
  `DATABASE_URL` env var, plus set `SECRET_KEY`.

---

## API quick tour

All endpoints are under `/api/v1`. Auth uses OAuth2 password flow (bearer token).

```bash
BASE=http://localhost:8000/api/v1

# Register (password: 8+ chars, 1 upper, 1 number, 1 special)
curl -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"chef@example.com","password":"Tasty1!meal","dietary_preference":"Vegetarian"}'

# Login -> token (note: form-encoded, "username" = email)
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -d "username=chef@example.com&password=Tasty1!meal" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Add an ingredient (expiry must be a future DD/MM/YYYY date, quantity > 0)
curl -X POST $BASE/ingredients -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Tomato","quantity":4,"expiry_date":"31/12/2026"}'

# Get recipe recommendations from your inventory
curl $BASE/recipes/recommendations -H "Authorization: Bearer $TOKEN"

# Detect ingredients from a photo
curl -X POST $BASE/images/detect -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/groceries.jpg"
```

---

## Wiring up real AI

`app/services/detection.py` currently returns deterministic placeholder
detections. To use a real model, replace the body of `detect_ingredients(...)`
with a call to your vision service (a hosted classifier, AWS Rekognition, a
custom PyTorch/TensorFlow model, or a multimodal LLM). The return shape
(`list[DetectedIngredient]`) is all the rest of the app depends on, so no other
code needs to change.

---

## Notes on the data rules

- **IDs** (`U001`, `ING001`, `REC001`, `SL001`, `P0001`, `CM0001`) are generated
  atomically via an `id_counters` table (`app/core/ids.py`) using
  `SELECT ... FOR UPDATE`, so they stay sequential and gap-free under concurrency.
- **Expiry dates** are accepted as `DD/MM/YYYY` strings, validated to be in the
  future, stored as `DATE`, and returned with both `expiry_date_display`
  (DD/MM/YYYY) and a computed `days_until_expiry`.
- **Enums** (`DietaryPreference`, `RecipeCategory`) are enforced at the schema
  layer — invalid values return HTTP 422.
```
