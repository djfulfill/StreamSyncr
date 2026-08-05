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

check_service() {
    local name="$1"
    local pid_file="$2"
    local port="$3"
    local pid=""

    if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        pid="$(cat "$pid_file")"
    elif PID=$(lsof -ti :$port 2>/dev/null || true); then
        :
    fi

    if [[ -z "$pid" ]]; then
        echo "🔴 $name — NOT running (port $port)"
        return 1
    fi

    echo "🟢 $name — RUNNING (PID: $pid, port $port)"
    return 0
}

echo "════════════════════════════════════════════════"
echo "  StreamSyncr Services"
echo "════════════════════════════════════════════════"

any_running=false
check_service "Backend"      "$BACKEND_PID"  "$BACKEND_PORT"  && any_running=true
check_service "Frontend"     "$FRONTEND_PID" "$FRONTEND_PORT" && any_running=true
check_service "IMDb Proxy"   "$IMDB_PID"     "$IMDB_PORT"     && any_running=true

echo "════════════════════════════════════════════════"

if $any_running; then
    echo ""
    echo "  Configure UI:  http://localhost:$BACKEND_PORT/configure"
    echo "  Frontend App:  http://localhost:$FRONTEND_PORT"
    exit 0
else
    exit 1
fi
