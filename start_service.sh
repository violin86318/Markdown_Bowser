#!/bin/bash
# Markdown Bowser + Cloudflare Tunnel Master Service Script
# This is called directly by the launchd service to keep both the Python
# server and the Cloudflare Tunnel running.

# This is copied and executed from ~/.markdown-bowser to bypass TCC restrictions.

DAEMON_DIR="${HOME}/.markdown-bowser"
PROJECT_DIR="/Users/wanglingwei/Documents/Antigravity/websites/Markdown_Bowser"

# Source User Config
if [ ! -f "${PROJECT_DIR}/config.sh" ]; then
    echo "❌ Error: config.sh not found in project directory!"
    exit 1
fi
source "${PROJECT_DIR}/config.sh"

mkdir -p "${DAEMON_DIR}/logs"
SERVER_LOG="${DAEMON_DIR}/logs/markdown-bowser.log"
TUNNEL_LOG="${DAEMON_DIR}/logs/tunnel.log"
LOCAL_BIN="${PROJECT_DIR}/bin"

# 0. Export PATHs so launchd can find python AND local cloudflared
export PATH="${LOCAL_BIN}:/opt/homebrew/bin:/usr/local/bin:$PATH"

# Export Proxies so cloudflared can connect to the internet
export https_proxy=http://127.0.0.1:8234
export http_proxy=http://127.0.0.1:8234
export all_proxy=socks5://127.0.0.1:8235
export HTTPS_PROXY=http://127.0.0.1:8234
export HTTP_PROXY=http://127.0.0.1:8234
export ALL_PROXY=socks5://127.0.0.1:8235

echo "[$(date)] Starting Services..."

# 1. Stop old instances
lsof -ti :8642 | xargs kill -9 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true

# 2. Start Python server in the background
ALLOW_ARGS=()
if [ -n "${ALLOWED_ROOTS:-}" ]; then
    ALLOW_ARGS=(--allow "${ALLOWED_ROOTS}")
fi

/opt/anaconda3/bin/python3 "${DAEMON_DIR}/server.py" \
    --host "0.0.0.0" \
    --port "8642" \
    --root "${TARGET_ROOT}" \
    --auth "${AUTH_CREDS}" \
    "${ALLOW_ARGS[@]}" > "$SERVER_LOG" 2>&1 &

# Wait for server to bind
sleep 3

# 3. Start Cloudflare Tunnel in the foreground (blocks so launchd considers it alive)
# Extract the trycloudflare URL and save it to the log clearly
echo "[$(date)] Launching Cloudflare Tunnel..." > "$TUNNEL_LOG"
cloudflared tunnel --url http://127.0.0.1:8642 2>&1 | tee -a "$TUNNEL_LOG"
