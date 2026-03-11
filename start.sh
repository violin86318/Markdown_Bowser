#!/bin/bash
# Markdown Bowser — Start Service
# Starts the server as a background process using nohup.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Try to load user config
CFG_FILE="${SCRIPT_DIR}/config.sh"
if [ ! -f "$CFG_FILE" ]; then
    echo "❌ Error: config.sh not found. Please copy config.example.sh to config.sh and configure your paths."
    exit 1
fi
source "$CFG_FILE"

LOG_FILE="${SCRIPT_DIR}/markdown-bowser.log"
PID_FILE="${SCRIPT_DIR}/.server.pid"

mkdir -p "$(dirname "$LOG_FILE")"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Markdown Bowser is already running (PID: $OLD_PID)"
        exit 0
    fi
fi

# Stop any lingering processes on port 8642
lsof -ti :8642 | xargs kill -9 2>/dev/null || true

# Start server
echo "🚀 Starting Markdown Bowser background service..."
nohup /opt/anaconda3/bin/python3 "${SCRIPT_DIR}/server.py" \
    --host "0.0.0.0" \
    --port "8642" \
    --root "${TARGET_ROOT}" \
    --auth "${AUTH_CREDS}" > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PID_FILE"

sleep 1

if kill -0 "$NEW_PID" > /dev/null 2>&1; then
    echo "✅ Markdown Bowser service started! (PID: $NEW_PID)"
else
    echo "❌ Failed to start service. Check logs: $LOG_FILE"
    exit 1
fi

echo "📂 Root: ${TARGET_ROOT}"
echo ""

# Show LAN IPs
echo "📱 Mobile access URLs:"
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print "   http://" $2 ":8642"}'
echo ""
echo "🔍 Logs: tail -f $LOG_FILE"
echo "🛑 Stop: bash ${SCRIPT_DIR}/stop.sh"
