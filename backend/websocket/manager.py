"""
Agent Arena — WebSocket Connection Manager
============================================
Manages per-match and lobby WebSocket connections with heartbeat monitoring.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("arena.websocket")

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 15
# If no pong received within this many seconds, consider stale
STALE_TIMEOUT = 45


@dataclass
class WSConnection:
    """Tracks a single WebSocket client."""
    ws: WebSocket
    connection_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    connected_at: float = field(default_factory=time.time)
    last_pong: float = field(default_factory=time.time)
    is_alive: bool = True

    async def send_json(self, data: dict[str, Any]) -> bool:
        """Send JSON to this connection. Returns False if failed."""
        if not self.is_alive:
            return False
        try:
            await self.ws.send_json(data)
            return True
        except Exception:
            self.is_alive = False
            return False

    async def send_text(self, text: str) -> bool:
        if not self.is_alive:
            return False
        try:
            await self.ws.send_text(text)
            return True
        except Exception:
            self.is_alive = False
            return False


class ConnectionManager:
    """
    Manages WebSocket connections for the Agent Arena.

    Two pools:
      - lobby_connections: anyone watching the lobby / general feed
      - match_connections: keyed by match_id, viewers of a specific match
    """

    def __init__(self) -> None:
        # Lobby watchers
        self.lobby_connections: dict[str, WSConnection] = {}
        # Match viewers: match_id -> {connection_id -> WSConnection}
        self.match_connections: dict[str, dict[str, WSConnection]] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False

    # ── Lifecycle ──────────────────────────────────────────────

    async def start(self) -> None:
        """Start the heartbeat background task."""
        if self._running:
            return
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("ConnectionManager started (heartbeat every %ds)", HEARTBEAT_INTERVAL)

    async def stop(self) -> None:
        """Stop heartbeat and close all connections."""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        # Close all connections
        for conn in list(self.lobby_connections.values()):
            try:
                await conn.ws.close()
            except Exception:
                pass
        for match_conns in self.match_connections.values():
            for conn in list(match_conns.values()):
                try:
                    await conn.ws.close()
                except Exception:
                    pass
        self.lobby_connections.clear()
        self.match_connections.clear()
        logger.info("ConnectionManager stopped")

    # ── Connect / Disconnect ───────────────────────────────────

    async def connect_lobby(self, websocket: WebSocket) -> WSConnection:
        """Accept and register a lobby WebSocket."""
        await websocket.accept()
        conn = WSConnection(ws=websocket)
        self.lobby_connections[conn.connection_id] = conn
        logger.info("Lobby connect: %s (total: %d)", conn.connection_id, len(self.lobby_connections))
        return conn

    async def connect_match(self, websocket: WebSocket, match_id: str) -> WSConnection:
        """Accept and register a match viewer WebSocket."""
        await websocket.accept()
        conn = WSConnection(ws=websocket)
        if match_id not in self.match_connections:
            self.match_connections[match_id] = {}
        self.match_connections[match_id][conn.connection_id] = conn
        count = len(self.match_connections[match_id])
        logger.info("Match %s viewer connect: %s (viewers: %d)", match_id, conn.connection_id, count)
        return conn

    async def disconnect_lobby(self, connection_id: str) -> None:
        """Remove a lobby connection."""
        self.lobby_connections.pop(connection_id, None)
        logger.info("Lobby disconnect: %s (total: %d)", connection_id, len(self.lobby_connections))

    async def disconnect_match(self, match_id: str, connection_id: str) -> None:
        """Remove a match viewer connection."""
        if match_id in self.match_connections:
            self.match_connections[match_id].pop(connection_id, None)
            if not self.match_connections[match_id]:
                del self.match_connections[match_id]
            logger.info("Match %s viewer disconnect: %s", match_id, connection_id)

    # ── Broadcasting ───────────────────────────────────────────

    def _make_message(self, event: str, data: Any, match_id: Optional[str] = None) -> dict[str, Any]:
        return {
            "type": event,
            "matchId": match_id,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def broadcast_to_lobby(self, event: str, data: Any) -> int:
        """Broadcast to all lobby connections. Returns count of successful sends."""
        msg = self._make_message(event, data)
        sent = 0
        stale: list[str] = []
        for cid, conn in list(self.lobby_connections.items()):
            if await conn.send_json(msg):
                sent += 1
            else:
                stale.append(cid)
        for cid in stale:
            await self.disconnect_lobby(cid)
        return sent

    async def broadcast_to_match(self, match_id: str, event: str, data: Any) -> int:
        """Broadcast to all viewers of a specific match."""
        msg = self._make_message(event, data, match_id=match_id)
        conns = self.match_connections.get(match_id, {})
        sent = 0
        stale: list[str] = []
        for cid, conn in list(conns.items()):
            if await conn.send_json(msg):
                sent += 1
            else:
                stale.append(cid)
        for cid in stale:
            await self.disconnect_match(match_id, cid)
        return sent

    async def broadcast_match_event(self, match_id: str, event: str, data: Any) -> None:
        """
        Broadcast a match event to both match viewers AND lobby.
        Events: round_start, agent_action, round_end, match_end
        """
        await self.broadcast_to_match(match_id, event, data)
        # Also push to lobby so they see live activity
        await self.broadcast_to_lobby(event, {**data, "matchId": match_id} if isinstance(data, dict) else data)

    # ── Specific Event Helpers ─────────────────────────────────

    async def emit_round_start(self, match_id: str, round_data: dict[str, Any]) -> None:
        await self.broadcast_match_event(match_id, "round:start", round_data)

    async def emit_agent_action(self, match_id: str, agent_id: str, action: str, partial: str = "") -> None:
        await self.broadcast_match_event(match_id, "round:response", {
            "matchId": match_id,
            "agent": agent_id,
            "action": action,
            "partialResponse": partial,
        })

    async def emit_round_end(self, match_id: str, round_data: dict[str, Any]) -> None:
        await self.broadcast_match_event(match_id, "round:end", round_data)

    async def emit_match_end(self, match_id: str, match_data: dict[str, Any]) -> None:
        await self.broadcast_match_event(match_id, "match:end", match_data)

    # ── Heartbeat ──────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """Periodically ping all connections and remove stale ones."""
        while self._running:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                now = time.time()

                # Check lobby connections
                stale_lobby: list[str] = []
                for cid, conn in list(self.lobby_connections.items()):
                    if now - conn.last_pong > STALE_TIMEOUT:
                        stale_lobby.append(cid)
                        continue
                    try:
                        await conn.ws.send_json({"type": "ping", "timestamp": datetime.now(timezone.utc).isoformat()})
                    except Exception:
                        stale_lobby.append(cid)
                for cid in stale_lobby:
                    await self.disconnect_lobby(cid)
                    logger.debug("Removed stale lobby connection: %s", cid)

                # Check match connections
                for match_id in list(self.match_connections.keys()):
                    stale_match: list[str] = []
                    for cid, conn in list(self.match_connections.get(match_id, {}).items()):
                        if now - conn.last_pong > STALE_TIMEOUT:
                            stale_match.append(cid)
                            continue
                        try:
                            await conn.ws.send_json({"type": "ping", "timestamp": datetime.now(timezone.utc).isoformat()})
                        except Exception:
                            stale_match.append(cid)
                    for cid in stale_match:
                        await self.disconnect_match(match_id, cid)
                        logger.debug("Removed stale match %s viewer: %s", match_id, cid)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Heartbeat loop error")

    def handle_pong(self, connection_id: str) -> None:
        """Update last_pong for a connection (call from WS handler on 'pong' message)."""
        for conn in self.lobby_connections.values():
            if conn.connection_id == connection_id:
                conn.last_pong = time.time()
                return
        for match_conns in self.match_connections.values():
            for conn in match_conns.values():
                if conn.connection_id == connection_id:
                    conn.last_pong = time.time()
                    return

    # ── Stats ──────────────────────────────────────────────────

    @property
    def lobby_viewer_count(self) -> int:
        return len(self.lobby_connections)

    def match_viewer_count(self, match_id: str) -> int:
        return len(self.match_connections.get(match_id, {}))

    @property
    def total_connections(self) -> int:
        return len(self.lobby_connections) + sum(
            len(conns) for conns in self.match_connections.values()
        )


# Singleton instance
manager = ConnectionManager()
