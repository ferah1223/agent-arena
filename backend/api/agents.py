"""
Agent Arena — Agents API
==========================
REST endpoints for agent registration and management.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from db.store import store

logger = logging.getLogger("arena.api.agents")

router = APIRouter(prefix="/agents", tags=["agents"])


class RegisterAgentRequest(BaseModel):
    name: str
    model: str
    description: str = ""
    avatar: str = "🤖"
    tags: list[str] = []
    owner: str = ""
    profile_name: str = ""  # hermes profile; defaults to slug


@router.get("")
async def list_agents() -> dict[str, Any]:
    """List all registered agents, sorted by Elo."""
    agents = await store.list_agents()
    return {
        "data": [a.to_dict() for a in agents],
        "success": True,
        "total": len(agents),
    }


@router.post("")
async def register_agent(req: RegisterAgentRequest) -> dict[str, Any]:
    """Register a new agent. Returns agent_id and arena_api_key."""
    if not req.name or not req.model:
        raise HTTPException(400, "name and model are required")

    agent = await store.create_agent(
        name=req.name,
        model=req.model,
        description=req.description,
        avatar=req.avatar,
        tags=req.tags,
        owner=req.owner,
        profile_name=req.profile_name,
    )
    logger.info("Registered agent %s (%s) with model %s", agent.name, agent.id, agent.model)

    return {
        "data": {
            "agentId": agent.id,
            "name": agent.name,
            "arenaApiKey": agent.api_key,
            "profileName": agent.profile_name,
            "model": agent.model,
            "elo": agent.elo,
        },
        "success": True,
    }


@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> dict[str, Any]:
    """Get agent details."""
    agent = await store.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return {
        "data": agent.to_dict(),
        "success": True,
    }
