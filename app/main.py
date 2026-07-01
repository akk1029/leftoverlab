"""FastAPI application entrypoint for LeftoverLab."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.api import api_router
from app.config import settings
from app.database import Base, engine

# Bundled minimal web UI lives in <project_root>/static.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Import models so their tables register on Base.metadata before create_all.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For a starter project we auto-create tables on startup. For real migrations,
    # use Alembic (`alembic upgrade head`) and remove this create_all call.
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=__version__,
        description="AI-Powered Smart Kitchen & Meal Planner API",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/info", tags=["health"])
    def info() -> dict:
        return {
            "name": settings.PROJECT_NAME,
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    # Serve the bundled minimal web UI (if present).
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        @app.get("/", include_in_schema=False)
        def ui() -> FileResponse:
            return FileResponse(STATIC_DIR / "index.html")
    else:
        @app.get("/", tags=["health"])
        def root() -> dict:
            return {"name": settings.PROJECT_NAME, "docs": "/docs"}

    return app


app = create_app()
