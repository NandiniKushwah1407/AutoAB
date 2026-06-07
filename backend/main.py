from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from database import create_tables
from routers import experiments, events, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup: create all DB tables."""
    await create_tables()
    yield


app = FastAPI(
    title="AutoAB API",
    description="Automated A/B Testing Platform — Self-driving experimentation engine",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow React dashboard to connect) ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve the JS SDK as a static file ─────────────────────────
sdk_path = os.path.join(os.path.dirname(__file__), "..", "sdk")
if os.path.isdir(sdk_path):
    app.mount("/sdk.js", StaticFiles(directory=sdk_path), name="sdk")

# ── Routers ───────────────────────────────────────────────────
app.include_router(experiments.router)
app.include_router(events.router)
app.include_router(analysis.router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "AutoAB API", "version": "1.0.0"}


@app.get("/", tags=["system"])
async def root():
    return {
        "message": "AutoAB — Automated A/B Testing Platform",
        "docs": "/docs",
        "health": "/health",
    }
