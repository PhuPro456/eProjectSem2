from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.db.init_db import initialize_database

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(
    title="BookStore API",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


if (DIST_DIR / "index.html").is_file():
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="frontend")
elif FRONTEND_DIR.is_dir():
    # React app not built yet (npm run build) — keep the legacy vanilla app
    # reachable at /legacy/ until then.
    @app.get("/", include_in_schema=False)
    def legacy_home() -> RedirectResponse:
        return RedirectResponse("/legacy/")

    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
