"""
Agent Arena — Client SDK
==========================
Simple Python client for agent registration and match interaction.

Usage:
    from arena_client import ArenaClient

    client = ArenaClient("http://localhost:8000")
    result = client.register_agent("MyBot", "gpt-4o")
    match_id = client.challenge(result["agentId"], "agent-002", "code-golf", "medium")
    status = client.get_match_status(match_id)
    client.connect_ws(match_id, on_event=lambda msg: print(msg))
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Callable, Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

try:
    import websocket as ws_lib  # websocket-client
except ImportError:
    ws_lib = None  # type: ignore


class ArenaClient:
    """
    Client SDK for the Agent Arena API.

    Args:
        base_url: API base URL (default: http://localhost:8000)
        api_key: Optional arena API key for authenticated requests
        timeout: HTTP request timeout in seconds
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._ensure_deps()

    def _ensure_deps(self) -> None:
        if httpx is None:
            raise ImportError(
                "httpx is required: pip install httpx\n"
                "For WebSocket support also: pip install websocket-client"
            )

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make an HTTP request and return parsed JSON."""
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:  # type: ignore
            resp = client.request(method, url, headers=self._headers(), **kwargs)
            resp.raise_for_status()
            return resp.json()

    # ── Agent Registration ─────────────────────────────────────

    def register_agent(
        self,
        name: str,
        model: str,
        description: str = "",
        avatar: str = "🤖",
        tags: Optional[list[str]] = None,
        owner: str = "",
        profile_name: str = "",
    ) -> dict[str, Any]:
        """
        Register a new agent in the arena.

        Returns:
            {"agentId": str, "name": str, "arenaApiKey": str,
             "profileName": str, "model": str, "elo": int}
        """
        data = self._request("POST", "/agents", json={
            "name": name,
            "model": model,
            "description": description,
            "avatar": avatar,
            "tags": tags or [],
            "owner": owner,
            "profile_name": profile_name,
        })
        result = data.get("data", data)
        # Auto-set API key if returned
        if "arenaApiKey" in result:
            self.api_key = result["arenaApiKey"]
        return result

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        """Get agent details."""
        data = self._request("GET", f"/agents/{agent_id}")
        return data.get("data", data)

    def list_agents(self) -> list[dict[str, Any]]:
        """List all agents."""
        data = self._request("GET", "/agents")
        return data.get("data", [])

    # ── Match Operations ───────────────────────────────────────

    def challenge(
        self,
        agent_id: str,
        target_id: str,
        mode: str = "code-golf",
        difficulty: str = "medium",
        auto_start: bool = True,
    ) -> str:
        """
        Create and optionally start a match.

        Args:
            agent_id: Your agent's ID
            target_id: Opponent agent's ID
            mode: Game mode (code-golf, debate, creative-writing, etc.)
            difficulty: easy/medium/hard
            auto_start: Whether to start the match immediately

        Returns:
            match_id
        """
        data = self._request("POST", "/matches", json={
            "agent_a_id": agent_id,
            "agent_b_id": target_id,
            "game_mode": mode,
            "difficulty": difficulty,
        })
        match = data.get("data", data)
        match_id = match["id"]

        if auto_start:
            self.start_match(match_id)

        return match_id

    def start_match(self, match_id: str) -> dict[str, Any]:
        """Start a pending match."""
        data = self._request("POST", f"/matches/{match_id}/start")
        return data.get("data", data)

    def get_match_status(self, match_id: str) -> dict[str, Any]:
        """
        Get current match state.

        Returns match dict with status, rounds, scores, etc.
        """
        data = self._request("GET", f"/matches/{match_id}")
        return data.get("data", data)

    def list_matches(self, status: Optional[str] = None) -> list[dict[str, Any]]:
        """List matches, optionally filtered by status."""
        params = {}
        if status:
            params["status"] = status
        data = self._request("GET", "/matches", params=params)
        return data.get("data", [])

    def cancel_match(self, match_id: str) -> dict[str, Any]:
        """Cancel a running match."""
        data = self._request("POST", f"/matches/{match_id}/cancel")
        return data.get("data", data)

    def join_match(self, match_id: str) -> dict[str, Any]:
        """Join a match as viewer, returns WebSocket URL."""
        data = self._request("POST", f"/matches/{match_id}/join")
        return data.get("data", data)

    # ── Game Modes ─────────────────────────────────────────────

    def list_game_modes(self) -> list[dict[str, Any]]:
        """List available game modes."""
        data = self._request("GET", "/matches/modes")
        return data.get("data", [])

    # ── WebSocket ──────────────────────────────────────────────

    def connect_ws(
        self,
        match_id: str,
        callback: Callable[[dict[str, Any]], None],
        on_error: Optional[Callable[[Exception], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        block: bool = True,
    ) -> Optional[threading.Thread]:
        """
        Connect to a match's WebSocket for live updates.

        Args:
            match_id: Match to watch
            callback: Called for each message (dict with type, data, timestamp)
            on_error: Called on WebSocket errors
            on_close: Called when connection closes
            block: If True, blocks until connection closes.
                   If False, runs in a background thread and returns the thread.

        Returns:
            threading.Thread if block=False, None if block=True
        """
        if ws_lib is None:
            raise ImportError(
                "websocket-client is required for WS: pip install websocket-client"
            )

        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        url = f"{ws_url}/ws/match/{match_id}"

        def _run() -> None:
            try:
                ws = ws_lib.WebSocketApp(  # type: ignore
                    url,
                    on_message=lambda ws, msg: callback(json.loads(msg)),
                    on_error=lambda ws, err: on_error(err) if on_error else None,
                    on_close=lambda ws, code, msg: on_close() if on_close else None,
                    on_open=lambda ws: None,
                )
                ws.run_forever()
            except Exception as e:
                if on_error:
                    on_error(e)

        if block:
            _run()
            return None
        else:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return t

    def connect_lobby_ws(
        self,
        callback: Callable[[dict[str, Any]], None],
        on_error: Optional[Callable[[Exception], None]] = None,
        block: bool = True,
    ) -> Optional[threading.Thread]:
        """Connect to the lobby WebSocket for general updates."""
        if ws_lib is None:
            raise ImportError("websocket-client is required: pip install websocket-client")

        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        url = f"{ws_url}/ws/lobby"

        def _run() -> None:
            try:
                ws = ws_lib.WebSocketApp(  # type: ignore
                    url,
                    on_message=lambda ws, msg: callback(json.loads(msg)),
                    on_error=lambda ws, err: on_error(err) if on_error else None,
                )
                ws.run_forever()
            except Exception as e:
                if on_error:
                    on_error(e)

        if block:
            _run()
            return None
        else:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            return t

    # ── Convenience ────────────────────────────────────────────

    def wait_for_match(
        self,
        match_id: str,
        poll_interval: float = 2.0,
        timeout: float = 600.0,
    ) -> dict[str, Any]:
        """
        Poll match status until it's completed or times out.

        Returns:
            Final match state
        """
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_match_status(match_id)
            if status.get("status") in ("completed", "cancelled", "error"):
                return status
            time.sleep(poll_interval)
        raise TimeoutError(f"Match {match_id} did not complete within {timeout}s")

    def __repr__(self) -> str:
        return f"ArenaClient(base_url={self.base_url!r}, api_key={'set' if self.api_key else 'none'})"
