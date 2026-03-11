#!/bin/bash
# Markdown Bowser — Stop Service
# Stops the background server process.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.server.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" > /dev/null 2>&1; then
        kill "$PID"
        echo "✅ Markdown Bowser service stopped (PID: $PID)."
    else
        echo "ℹ️  Service was not running (stale PID file)."
    fi
    rm -f "$PID_FILE"
else
    # Fallback to kill by port/name
    PIDS=$(lsof -ti :8642 2>/dev/null || true)
    if [ ! -z "$PIDS" ]; then
        kill $PIDS
        echo "✅ Markdown Bowser service stopped (Port 8642)."
    else
        echo "ℹ️  Service was not running."
    fi
fi

echo "🛑 Done."
