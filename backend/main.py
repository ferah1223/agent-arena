"""
Agent Arena — FastAPI Application
===================================
Main entry point. Integrates all API routes, WebSocket endpoints,
and manages the match engine lifecycle.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.agents import router as agents_router
from api.matches import router as matches_router
from api.leaderboard import router as leaderboard_router
from websocket.routes import router as ws_router
from websocket.manager import manager as ws_manager

# ── Logging Setup ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("arena")


# ── Lifespan (startup / shutdown) ──────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: start WS manager, clean up on shutdown."""
    logger.info("Agent Arena starting up...")
    await ws_manager.start()
    logger.info("WebSocket ConnectionManager ready (heartbeat active)")
    logger.info("Match engine ready (max %d concurrent matches)", 5)
    yield
    logger.info("Agent Arena shutting down...")
    await ws_manager.stop()
    logger.info("Cleanup complete")


# ── App Factory ────────────────────────────────────────────────

app = FastAPI(
    title="Agent Arena",
    version="1.0.0",
    description="AI agent competition platform — watch agents battle in real-time.",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routes ────────────────────────────────────────────

app.include_router(agents_router)
app.include_router(matches_router)
app.include_router(leaderboard_router)
app.include_router(ws_router)


# ── Health & Info ──────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": "1.0.0",
        "websocket_connections": ws_manager.total_connections,
    }


@app.get("/")
async def root() -> dict:
    return {
        "name": "Agent Arena API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "agents": "/agents",
            "matches": "/matches",
            "game_modes": "/matches/modes",
            "ws_match": "/ws/match/{match_id}",
            "ws_lobby": "/ws/lobby",
        },
    }


# ── Run with: python -m backend.main ──────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
