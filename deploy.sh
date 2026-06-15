#!/usr/bin/env bash
set -euo pipefail

ARENA_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT="${ARENA_PORT:-8000}"
FRONTEND_PORT=3000

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }

echo ""
echo "=============================="
echo "  Agent Arena — Deploy"
echo "=============================="
echo ""

# ── load env if present ──
if [ -f "$ARENA_DIR/.env" ]; then
    set -a
    source "$ARENA_DIR/.env"
    set +a
    info "Loaded .env"
fi

# ── check screen is available ──
if ! command -v screen &>/dev/null; then
    err "screen not found — install it: sudo apt install screen"
    exit 1
fi

# ── kill existing sessions if running ──
for sess in arena-backend arena-frontend; do
    if screen -list | grep -q "$sess"; then
        warn "Killing existing session: $sess"
        screen -S "$sess" -X quit 2>/dev/null || true
        sleep 1
    fi
done

# ── start backend ──
info "Starting backend on :${BACKEND_PORT} …"
screen -dmS arena-backend bash -c "
    cd '$ARENA_DIR/backend'
    exec uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload
"
sleep 2

# ── start frontend ──
info "Starting frontend on :${FRONTEND_PORT} …"
screen -dmS arena-frontend bash -c "
    cd '$ARENA_DIR'
    exec npm run dev -- --port $FRONTEND_PORT
"
sleep 3

# ── verify ──
echo ""
echo "── Status ──────────────────────"

ok=true

if screen -list | grep -q "arena-backend"; then
    info "arena-backend  — screen session running"
else
    err  "arena-backend  — screen session NOT found"
    ok=false
fi

if screen -list | grep -q "arena-frontend"; then
    info "arena-frontend — screen session running"
else
    err  "arena-frontend — screen session NOT found"
    ok=false
fi

# quick port check
for port in $BACKEND_PORT $FRONTEND_PORT; do
    if ss -tlnp | grep -q ":${port} "; then
        info "Port $port is listening"
    else
        warn "Port $port not yet listening (may still be starting)"
    fi
done

echo ""
if $ok; then
    info "All services launched. Attach with: screen -r arena-backend / arena-frontend"
else
    err "Some services failed to start. Check logs: screen -r <session>"
fi
echo ""
