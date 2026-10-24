"""The `web` service: API + (in production) the built React site. Owner: Bereket.

uv run uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import company, events, links, me, phone, studies, watches, webhooks
from app.config import REPO_ROOT, settings
from app.db import init_db

logging.basicConfig(level=logging.INFO)
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Ticket Watch API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.public_web_url],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (watches, webhooks, phone, me, links, company, events, studies):
    app.include_router(module.router)
if settings.mock_whop:
    from app.api import dev

    app.include_router(dev.router)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "env": settings.app_env}


# Serve the built frontend (Docker/Railway). In dev, Vite serves it on :5173 instead.
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        file = FRONTEND_DIST / path
        if path and file.is_file() and FRONTEND_DIST in file.resolve().parents:
            return FileResponse(file)
        return FileResponse(Path(FRONTEND_DIST / "index.html"))
