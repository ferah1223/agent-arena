// ============================================================
// Agent Arena — WebSocket Client
// ============================================================

export type WSMessageHandler = (data: Record<string, unknown>) => void;

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL
  || (typeof window !== "undefined"
    ? `ws://${window.location.hostname}:8000`
    : "ws://localhost:8000");

const RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_ATTEMPTS = 10;

/**
 * Returns a WebSocket connection with auto-reconnect.
 * Call the returned cleanup function to close and stop reconnecting.
 */
function createReconnectingWS(
  url: string,
  onMessage: WSMessageHandler,
  onOpen?: () => void,
  onClose?: () => void,
): () => void {
  let ws: WebSocket | null = null;
  let attempts = 0;
  let closed = false;
  let pingInterval: ReturnType<typeof setInterval> | null = null;

  function connect() {
    if (closed) return;

    ws = new WebSocket(url);

    ws.onopen = () => {
      attempts = 0;
      onOpen?.();

      // Send periodic pong-like keepalive (server sends ping frames)
      pingInterval = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "pong" }));
        }
      }, 30_000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string);
        if (data.type === "ping") {
          // Respond to server ping
          ws?.send(JSON.stringify({ type: "pong" }));
          return;
        }
        onMessage(data);
      } catch {
        // not JSON — ignore
      }
    };

    ws.onclose = () => {
      if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
      }
      onClose?.();

      if (!closed && attempts < MAX_RECONNECT_ATTEMPTS) {
        attempts++;
        const delay = RECONNECT_DELAY_MS * Math.min(attempts, 5);
        setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      // onclose will fire after onerror — reconnect handled there
      ws?.close();
    };
  }

  connect();

  // Return cleanup function
  return () => {
    closed = true;
    if (pingInterval) {
      clearInterval(pingInterval);
      pingInterval = null;
    }
    if (ws) {
      ws.close();
      ws = null;
    }
  };
}

/**
 * Connect to a live match WebSocket.
 * Returns a cleanup function to disconnect.
 */
export function connectToMatch(
  matchId: string,
  onMessage: WSMessageHandler,
  onOpen?: () => void,
  onClose?: () => void,
): () => void {
  const url = `${WS_BASE}/ws/match/${matchId}`;
  return createReconnectingWS(url, onMessage, onOpen, onClose);
}

/**
 * Connect to the lobby WebSocket.
 * Returns a cleanup function to disconnect.
 */
export function connectToLobby(
  onMessage: WSMessageHandler,
  onOpen?: () => void,
  onClose?: () => void,
): () => void {
  const url = `${WS_BASE}/ws/lobby`;
  return createReconnectingWS(url, onMessage, onOpen, onClose);
}
