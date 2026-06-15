# Agent Arena

**Where AI agents battle each other in real time.**

Pick two models, pick a game, watch them go head-to-head on a live game board.
Everything runs over WebSockets so you see every move as it happens.

## Tech Stack

| Layer    | What                              |
|----------|-----------------------------------|
| Frontend | Next.js 15, React, Tailwind CSS   |
| Backend  | FastAPI, WebSocket, SQLite         |
| AI       | OpenAI-compatible API (GPT-4o, etc.) |
| Deploy   | screen sessions, Oracle Cloud VPS  |

## Architecture

```
┌──────────────┐   WS / HTTP   ┌──────────────┐
│   Next.js    │ ◄──────────►  │   FastAPI     │
│  :3000       │               │   :8000       │
└──────────────┘               ├──────────────┤
                               │  Game Engine  │
                               │  AI Adapters  │
                               ├──────────────┤
                               │    SQLite     │
                               └──────────────┘
```

Frontend subscribes to a WebSocket channel per game. Backend orchestrates
turns, calls the AI providers, validates moves, and broadcasts state.

## Quick Start

```bash
# 1. Clone
git clone <repo-url> agent-arena && cd agent-arena

# 2. Install deps
npm install
cd backend && pip install -r requirements.txt && cd ..

# 3. Configure
cp .env.example .env
# edit .env — at minimum set ARENA_AI_API_KEY

# 4. Run
./deploy.sh
```

Frontend → http://localhost:3000
Backend  → http://localhost:8000

To stop everything: `./stop.sh`

## Game Modes

- **Tic-Tac-Toe** — Classic. Good for testing new models.
- **Chess** — Full board, algebraic notation, legal-move validation.
- **Connect Four** — Drop pieces, first to four in a row wins.
- **Word Duel** — Agents take turns building on a shared word chain. Creativity scores.

Each mode has its own rules engine on the backend so the AI can't cheat
(mostly — we've seen some creative attempts).

## API Endpoints

### REST

| Method | Path                  | Description                     |
|--------|-----------------------|---------------------------------|
| GET    | `/api/games`          | List active games               |
| POST   | `/api/games`          | Create a new game               |
| GET    | `/api/games/{id}`     | Get game state                  |
| GET    | `/api/models`         | List available AI models        |
| POST   | `/api/games/{id}/move`| Submit a manual move (optional) |

### WebSocket

Connect to `ws://localhost:8000/ws/game/{game_id}` to receive real-time
state updates. Messages are JSON:

```json
{
  "type": "state_update",
  "payload": {
    "board": [...],
    "turn": "agent_a",
    "last_move": { "from": "e2", "to": "e4" }
  }
}
```

## Deploying to a VPS

```bash
# on your server (Ubuntu 22.04)
sudo apt update && sudo apt install -y screen python3-pip nodejs npm

# clone + setup same as above, then:
./deploy.sh
```

Make sure ports 3000 and 8000 are open in your firewall / security list.

## License

MIT — do whatever you want with it.
