"""
Agent Arena — WebSocket Routes
================================
WS /ws/match/{match_id}  — live match viewer
WS /ws/lobby             — general lobby updates

Message format: {type, matchId, data, timestamp}
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from websocket.manager import manager

logger = logging.getLogger("arena.ws_routes")

router = APIRouter()


# ── Match Viewer WebSocket ─────────────────────────────────────

@router.websocket("/ws/match/{match_id}")
async def ws_match_viewer(websocket: WebSocket, match_id: str) -> None:
    """
    Live match viewer. Receives all events for a specific match.
    Client can send: {"type": "pong"} in response to server pings.
    """
    conn = await manager.connect_match(websocket, match_id)
    try:
        # Send initial connection confirmation
        await conn.send_json({
            "type": "connected",
            "matchId": match_id,
            "data": {
                "connectionId": conn.connection_id,
                "viewers": manager.match_viewer_count(match_id),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Listen for client messages (pong, chat, etc.)
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "pong":
                manager.handle_pong(conn.connection_id)
            elif msg_type == "chat":
                # Echo chat messages to all match viewers
                await manager.broadcast_to_match(match_id, "chat:message", {
                    "matchId": match_id,
                    "username": msg.get("username", "Anonymous"),
                    "message": msg.get("message", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            # Ignore unknown message types

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS match %s error", match_id)
    finally:
        await manager.disconnect_match(match_id, conn.connection_id)


# ── Lobby WebSocket ────────────────────────────────────────────

@router.websocket("/ws/lobby")
async def ws_lobby(websocket: WebSocket) -> None:
    """
    General lobby feed. Receives:
      - new match announcements
      - match results
      - leaderboard updates
    Client can send: {"type": "pong"} in response to server pings.
    """
    conn = await manager.connect_lobby(websocket)
    try:
        # Send initial connection confirmation
        await conn.send_json({
            "type": "connected",
            "matchId": None,
            "data": {
                "connectionId": conn.connection_id,
                "lobbyViewers": manager.lobby_viewer_count,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Listen for client messages
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "pong":
                manager.handle_pong(conn.connection_id)
            elif msg_type == "chat":
                await manager.broadcast_to_lobby("chat:message", {
                    "username": msg.get("username", "Anonymous"),
                    "message": msg.get("message", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            # Ignore unknown message types

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS lobby error")
    finally:
        await manager.disconnect_lobby(conn.connection_id)
