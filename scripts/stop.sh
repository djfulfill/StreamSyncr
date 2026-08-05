#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR"
BACKEND_PID="$PID_DIR/.streamsync.pid"
FRONTEND_PID="$PID_DIR/.frontend.pid"
IMDB_PID="$PID_DIR/.imdb_proxy.pid"
BACKEND_PORT=7800
FRONTEND_PORT=3030
IMDB_PORT=3031

stop_service() {
    local name="$1"
    local pid_file="$2"
    local port="$3"

    # Try PID file first
    if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        local pid
        pid="$(cat "$pid_file")"
        echo "🛑 Stopping $name (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
        echo "✅ $name stopped."
        return 0
    fi

    # Fallback: find by port
    local pid
    PID=$(lsof -ti :$port 2>/dev/null || true)
    if [[ -n "$PID" ]]; then
        echo "🛑 Stopping $name on port $port (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        sleep 1
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID" 2>/dev/null || true
        fi
        rm -f "$pid_file"
        echo "✅ $name stopped."
        return 0
    fi

    echo "ℹ️  $name not running."
    rm -f "$pid_file"
    return 0
}

stop_service "IMDb Proxy" "$IMDB_PID" "$IMDB_PORT"
stop_service "Frontend" "$FRONTEND_PID" "$FRONTEND_PORT"
stop_service "Backend" "$BACKEND_PID" "$BACKEND_PORT"

echo ""
echo "All StreamSyncr services stopped."
