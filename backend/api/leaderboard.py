"""
Agent Arena — Leaderboard API
================================
REST endpoints for the agent leaderboard.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Query

from db.store import store

logger = logging.getLogger("arena.api.leaderboard")

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("")
async def get_leaderboard(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Get the agent leaderboard, sorted by Elo rating."""
    agents = await store.list_agents()  # Already sorted by elo desc
    total = len(agents)
    start = (page - 1) * page_size
    end = start + page_size
    page_agents = agents[start:end]

    items = []
    for rank, agent in enumerate(page_agents, start=start + 1):
        a = agent.to_dict()
        a["rank"] = rank
        a["streak"] = 0  # TODO: calculate actual streak
        items.append(a)

    return {
        "data": items,
        "success": True,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": (total + page_size - 1) // page_size,
        },
    }
