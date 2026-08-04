#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.streamsync.pid"
PORT=7800

# ── Try PID file first ────────────────────────────────────────────
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    PID="$(cat "$PID_FILE")"
    echo "🛑 Stopping StreamSyncr (PID: $PID)..."
    kill "$PID"
    sleep 1
    if kill -0 "$PID" 2>/dev/null; then
        echo "⚠️  Force-killing PID $PID..."
        kill -9 "$PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "✅ Stopped."
    exit 0
fi

# ── Fallback: find by port ────────────────────────────────────────
PID=$(lsof -ti :$PORT 2>/dev/null || true)
if [[ -n "$PID" ]]; then
    echo "🛑 Stopping server on port $PORT (PID: $PID)..."
    kill "$PID"
    sleep 1
    if kill -0 "$PID" 2>/dev/null; then
        kill -9 "$PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "✅ Stopped."
    exit 0
fi

echo "⚠️  No running StreamSyncr server found."
rm -f "$PID_FILE"
exit 0