#!/bin/bash
# Stop and disable Markdown Bowser Auto-Start Service.
# Double-click this file or run it in your Terminal.

set -e

echo "🛑 Stopping Markdown Bowser Auto-Start Service..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.user.markdown-bowser.plist"
PLIST_DST="${HOME}/Library/LaunchAgents/${PLIST_NAME}"

if launchctl print gui/$(id -u) "${PLIST_DST}" 2>/dev/null | grep -q state; then
    echo "⚠️  Found running service, stopping..."
    launchctl bootout gui/$(id -u) "${PLIST_DST}" 2>/dev/null || true
    echo "✅ Service stopped."
else
    echo "ℹ️  Service is not currently loaded in launchd."
fi

# Fallback cleanup just in case any processes linger
pkill -f "cloudflared tunnel" 2>/dev/null || true
lsof -ti :8642 | xargs kill -9 2>/dev/null || true

# Remove plist to prevent future auto-starts
if [ -f "${PLIST_DST}" ]; then
    rm -f "${PLIST_DST}"
    echo "🗑️  Removed auto-start configuration."
fi
rm -f "${HOME}/.markdown-bowser/start_service.sh" 2>/dev/null || true

echo "======================================"
echo "🛑 SUCCESS: Markdown Bowser and Cloudflare Tunnel have fully stopped."
echo "It will no longer start when you boot your Mac."
echo "======================================"
