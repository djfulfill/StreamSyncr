#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ADDON_DIR="$PROJECT_DIR/addon"
APIS_DIR="$PROJECT_DIR/apis"
PID_FILE="$SCRIPT_DIR/.streamsync.pid"
PORT=7800

# ── Handle --restart ──────────────────────────────────────────────
if [[ "${1:-}" == "--restart" ]]; then
    echo "🔄 Restarting StreamSyncr server..."
    "$SCRIPT_DIR/stop.sh"
    sleep 1
fi

# ── Already running? ──────────────────────────────────────────────
if "$SCRIPT_DIR/status.sh" &>/dev/null; then
    echo "⚠️  StreamSyncr is already running on port $PORT"
    "$SCRIPT_DIR/status.sh"
    exit 0
fi

# ── Start the server ──────────────────────────────────────────────
echo "🚀 Starting StreamSyncr server on port $PORT..."
cd "$ADDON_DIR"

nohup python3 -c "
import sys, os
sys.path.insert(0, '$APIS_DIR')
sys.path.insert(0, '$ADDON_DIR')
from server import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=$PORT)
" > /dev/null 2>&1 &

echo $! > "$PID_FILE"
# strip any trailing newline from lsof in stop.sh
printf '%s' "$!" > "$PID_FILE"

sleep 2

# ── Verify it came up ─────────────────────────────────────────────
if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "✅ StreamSyncr started (PID: $(cat "$PID_FILE"))"
    echo "   http://localhost:$PORT/manifest.json"
else
    echo "❌ Failed to start. Check logs."
    rm -f "$PID_FILE"
    exit 1
fi