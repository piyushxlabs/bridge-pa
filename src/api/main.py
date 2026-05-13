from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import admin, session, specialist, workflow
from src.graph.graph_builder import initialize_graph

logger = structlog.get_logger(__name__)


# ── Lifespan handler ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup: swap graph to PostgreSQL checkpointer.
    Shutdown: log graceful shutdown.
    """
    try:
        await initialize_graph()
        logger.info("startup.graph_initialized_with_pg_checkpointer")
    except Exception as exc:
        logger.error("startup.graph_init_failed", error=str(exc))
        # Server continues with MemorySaver (degraded but functional)

    yield  # ← application runs here

    logger.info("shutdown.initiated")


# ── Application factory ────────────────────────────────────────────────────────
app = FastAPI(
    title="Bridge-PA Prior Authorization Orchestration API",
    description="HIPAA-compliant Prior Authorization (Concurrent Review) orchestration system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],   # Never wildcard in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(session.router)
app.include_router(workflow.router)
app.include_router(specialist.router)
app.include_router(admin.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """GET /health — returns 200 OK when server is running."""
    return {"status": "ok", "service": "bridge-pa"}

