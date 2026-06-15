#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "── Stopping Agent Arena ──"
echo ""

for sess in arena-backend arena-frontend; do
    if screen -list | grep -q "$sess"; then
        screen -S "$sess" -X quit 2>/dev/null || true
        echo -e "${GREEN}[✓]${NC} Killed $sess"
    else
        echo -e "${YELLOW}[!]${NC} $sess was not running"
    fi
done

echo ""
echo "Done."
