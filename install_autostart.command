#!/bin/bash
# Install and configure Markdown Bowser auto-start + Cloudflare Tunnel natively.
# Double-click this file or run it in your Terminal.

set -e

# Export Homebrew paths and Proxies for the double-clicked environment
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export https_proxy=http://127.0.0.1:8234
export http_proxy=http://127.0.0.1:8234
export all_proxy=socks5://127.0.0.1:8235
export HTTPS_PROXY=http://127.0.0.1:8234
export HTTP_PROXY=http://127.0.0.1:8234
export ALL_PROXY=socks5://127.0.0.1:8235

echo "🔧 Installing Markdown Bowser Auto-Start Service..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.user.markdown-bowser.plist"
PLIST_SRC="${SCRIPT_DIR}/${PLIST_NAME}"
PLIST_DST="${HOME}/Library/LaunchAgents/${PLIST_NAME}"

# Step 1: Install Cloudflared if missing
LOCAL_BIN="${SCRIPT_DIR}/bin"
mkdir -p "${LOCAL_BIN}"
if [ ! -f "${LOCAL_BIN}/cloudflared" ]; then
    echo "⬇️ Cloudflare Tunnel (cloudflared) not found. Downloading isolated binary..."
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        CF_FILE="cloudflared-darwin-arm64.tgz"
    else
        CF_FILE="cloudflared-darwin-amd64.tgz"
    fi
    CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/${CF_FILE}"
    PROXY_URL="https://mirror.ghproxy.com/${CF_URL}"
    
    cd "${LOCAL_BIN}"
    echo "Downloading from GitHub..."
    curl -L "$PROXY_URL" -o "${CF_FILE}" || curl -L "$CF_URL" -o "${CF_FILE}"
    tar -xzf "${CF_FILE}"
    rm "${CF_FILE}"
    chmod +x cloudflared
    cd "${SCRIPT_DIR}"
    echo "✅ cloudflared installed locally."
else
    echo "✅ cloudflared is already installed locally."
fi

# Step 2: Ensure plist is configured to point to our Start Script
DAEMON_DIR="${HOME}/.markdown-bowser"
mkdir -p "${DAEMON_DIR}/logs"

# Copy execution scripts to bypass macOS TCC Documents restrictions
cp "${SCRIPT_DIR}/start_service.sh" "${DAEMON_DIR}/start_service.sh"
cp "${SCRIPT_DIR}/server.py" "${DAEMON_DIR}/server.py"
chmod +x "${DAEMON_DIR}/start_service.sh"

cat <<EOF > "${PLIST_SRC}"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.markdown-bowser</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${DAEMON_DIR}/start_service.sh</string>
    </array>

    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${SCRIPT_DIR}/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${SCRIPT_DIR}/launchd.log</string>
</dict>
</plist>
EOF

# Step 3: Install the launchd plist
echo "📂 Copying LaunchAgent plist..."
mkdir -p "${HOME}/Library/LaunchAgents"

# Unload existing
launchctl unload "${PLIST_DST}" 2>/dev/null || true

rm -f "${PLIST_DST}" || true
cp "${PLIST_SRC}" "${PLIST_DST}"
chmod 644 "${PLIST_DST}"

# Step 4: Boot out the old state and Bootstrap 
echo "🚀 Bootstrapping Native Service..."
launchctl bootout gui/$(id -u) "${PLIST_DST}" 2>/dev/null || true
launchctl bootstrap gui/$(id -u) "${PLIST_DST}"

echo "======================================"
echo "🎉 SUCCESS: Service is now locked in!"
echo "It will automatically start every time you log into your Mac."
echo ""
echo "To check your public Intranet Penetration (Cloudflare) URL, run:"
echo "cat ${SCRIPT_DIR}/tunnel.log"
echo "======================================"
