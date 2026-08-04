#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.streamsync.pid"
PORT=7800
BASE_URL="http://localhost:$PORT"

# ── Check process ─────────────────────────────────────────────────
PID=""
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    PID="$(cat "$PID_FILE")"
elif PID=$(lsof -ti :$PORT 2>/dev/null || true); then
    :
fi

if [[ -z "$PID" ]]; then
    echo "🔴 StreamSyncr is NOT running (port $PORT)"
    exit 1
fi

echo "🟢 StreamSyncr is RUNNING"
echo "   PID:    $PID"
echo "   Port:   $PORT"

# ── Health check ───────────────────────────────────────────────────
MANIFEST=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/manifest.json" 2>/dev/null || echo "unreachable")
echo "   /manifest.json:  HTTP $MANIFEST"

if [[ "$MANIFEST" == "200" ]]; then
    echo "   Config UI:       $BASE_URL/configure"
fi

exit 0