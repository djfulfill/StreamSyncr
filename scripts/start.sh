#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ADDON_DIR="$PROJECT_DIR/addon"
APIS_DIR="$PROJECT_DIR/apis"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_DIR="$SCRIPT_DIR"
BACKEND_PID="$PID_DIR/.streamsync.pid"
FRONTEND_PID="$PID_DIR/.frontend.pid"
IMDB_PID="$PID_DIR/.imdb_proxy.pid"
BACKEND_PORT=7800
FRONTEND_PORT=3030
IMDB_PORT=3031

# ── Handle --restart ──────────────────────────────────────────────
if [[ "${1:-}" == "--restart" ]]; then
    echo "🔄 Restarting StreamSyncr services..."
    "$SCRIPT_DIR/stop.sh"
    sleep 1
fi

# ── Check if already running ──────────────────────────────────────
already_running() {
    local pid_file="$1"
    if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        return 0
    fi
    return 1
}

if already_running "$BACKEND_PID" && already_running "$FRONTEND_PID" && already_running "$IMDB_PID"; then
    echo "⚠️  All StreamSyncr services are already running"
    "$SCRIPT_DIR/status.sh"
    exit 0
fi

# ── Start IMDb proxy (Node.js, port 3031) ───────────────────────
if already_running "$IMDB_PID"; then
    echo "ℹ️  IMDb proxy already running (PID: $(cat "$IMDB_PID"))"
else
    echo "🚀 Starting IMDb proxy on port $IMDB_PORT..."
    cd "$FRONTEND_DIR"
    nohup node imdb_proxy.mjs > /dev/null 2>&1 &
    printf '%s' "$!" > "$IMDB_PID"
    sleep 1
    if kill -0 "$(cat "$IMDB_PID")" 2>/dev/null; then
        echo "✅ IMDb proxy started (PID: $(cat "$IMDB_PID"))"
    else
        echo "❌ Failed to start IMDb proxy"
        rm -f "$IMDB_PID"
    fi
fi

# ── Start backend server (FastAPI, port 7800) ───────────────────
if already_running "$BACKEND_PID"; then
    echo "ℹ️  Backend already running (PID: $(cat "$BACKEND_PID"))"
else
    echo "🚀 Starting backend on port $BACKEND_PORT..."
    cd "$ADDON_DIR"
    nohup python3 -c "
import sys, os
sys.path.insert(0, '$APIS_DIR')
sys.path.insert(0, '$ADDON_DIR')
from server import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=$BACKEND_PORT)
" > /dev/null 2>&1 &
    printf '%s' "$!" > "$BACKEND_PID"
    sleep 2
    if kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
        echo "✅ Backend started (PID: $(cat "$BACKEND_PID"))"
    else
        echo "❌ Failed to start backend"
        rm -f "$BACKEND_PID"
    fi
fi

# ── Start frontend dev server (Vite, port 3030) ─────────────────
if already_running "$FRONTEND_PID"; then
    echo "ℹ️  Frontend already running (PID: $(cat "$FRONTEND_PID"))"
else
    echo "🚀 Starting frontend on port $FRONTEND_PORT..."
    cd "$FRONTEND_DIR"
    nohup npx vite --host > /dev/null 2>&1 &
    printf '%s' "$!" > "$FRONTEND_PID"
    sleep 3
    if kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then
        echo "✅ Frontend started (PID: $(cat "$FRONTEND_PID"))"
    else
        echo "❌ Failed to start frontend"
        rm -f "$FRONTEND_PID"
    fi
fi

# ── Final status ─────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════"
echo "  StreamSyncr Services"
echo "════════════════════════════════════════════════"

all_ok=true

for name_pid in "Backend:$BACKEND_PID:$BACKEND_PORT" "Frontend:$FRONTEND_PID:$FRONTEND_PORT" "IMDb Proxy:$IMDB_PID:$IMDB_PORT"; do
    IFS=: read -r name pid_file port <<< "$name_pid"
    if already_running "$pid_file"; then
        echo "  ✅ $name — http://localhost:$port (PID: $(cat "$pid_file"))"
    else
        echo "  ❌ $name — FAILED"
        all_ok=false
    fi
done

echo "════════════════════════════════════════════════"
echo ""
echo "  Configure UI:  http://localhost:$BACKEND_PORT/configure"
echo "  Frontend App:  http://localhost:$FRONTEND_PORT"
echo ""

if $all_ok; then
    exit 0
else
    exit 1
fi
