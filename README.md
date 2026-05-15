# Markdown Bowser

A ultra-lightweight, zero-dependency (other than standard Python + `mistune` + `pygments`) Markdown preview server specifically designed for macOS, focusing on mobile responsiveness and seamless Cloudflare intranet penetration.

## ✨ Features

- **Mobile First Interface**: Renders directories and Markdown documents beautifully on desktop and mobile browsers.
- **GitHub Flavored Markdown**: Native syntax highlighting and table support.
- **Background Daemon**: Run it once, keep it running forever natively using `nohup` or `launchd`.
- **System Auto-Start**: Automatically configure macOS `launchd` and Cloudflare Tunnel (`cloudflared`) to run headlessly as a sandboxed system service on system boot.
- **Intranet Penetration**: Safely expose your local Markdown vault to the internet via Cloudflare without port forwarding.
- **HTTP Basic Auth**: Security gatekeeper preventing unauthorized public access.

---

## 🚀 Quick Start

### 1. Configure the Application
Copy the example configuration file and set your private parameters:
```bash
cp config.example.sh config.sh
nano config.sh
```
In `config.sh`, set your `TARGET_ROOT` (the folder holding your markdown notes) and your `AUTH_CREDS` (username:password) to protect your web interface. Each computer should use its own local absolute paths.

If you need to browse directories outside `TARGET_ROOT`, set `ALLOWED_ROOTS` to a comma-separated list of absolute paths for that computer. For example, a URL such as `/~Vibe-Coding/` normally means there is a `~Vibe-Coding` directory or symlink under `TARGET_ROOT`; if that symlink points outside `TARGET_ROOT`, add the real target path to `ALLOWED_ROOTS`.

### 2. Manual Start (Local Network)
If you just want to run the server temporarily in the background on your local network:
```bash
./start.sh
```
Check `markdown-bowser.log` for your IP address access links. Stop it anytime with `./stop.sh`.

---

## 🌍 Cloud-Native Auto-Start (The Good Stuff)

Want to turn your Mac into a persistent cloud note server? We built a native **auto-start installer** that runs your server explicitly and hooks it up to a free Cloudflare Tunnel so you can access your notes from anywhere in the world.

### Installation

Simply double click the `install_autostart.command` file from macOS Finder (or run it in terminal).

The script automates the following:
1. Downloads the `cloudflared` binary directly from GitHub releases locally to `bin/` (bypassing flaky Homebrew registries).
2. Clones the execution scripts to `~/.markdown-bowser/` (see "Technical Nuances" below).
3. Registers a `launchd` plist to start on macOS Boot.
4. Generates a public `xxx.trycloudflare.com` URL.

### Finding your Public URL

After successful installation, wait 5 seconds and read the network logs:
```bash
cat ~/.markdown-bowser/logs/tunnel.log
```
Look for the `https://xxxx.trycloudflare.com` link. Open it, enter your HTTP Basic Auth credentials, and view your notes securely!

To uninstall and clean up the background service, double-click `stop_autostart.command`.

---

## 🛠️ Technical Nuances & Battles Overcome

If you are a developer looking at the source code, you may wonder why things are structured in certain ways. Here are the hurdles we solved for macOS:

1. **macOS TCC (Transparency, Consent, and Control) Sandbox Limits**:
   macOS `launchd` strictly forbids background daemons from reading or writing to user privacy folders (`~/Documents`, `~/Desktop`, `~/Downloads`) without GUI prompts. This routinely causes background scripts (like `start_service.sh` and log files) to fail with an ominous `Operation not permitted`.
   - **The Fix**: The `install_autostart.command` deliberately quarantines the daemon scripts and logs into `~/.markdown-bowser/` (the user root), which is *not* protected by TCC.

2. **IPv6 vs IPv4 Bindings**:
   When binding Cloudflare Tunnel to `http://localhost:8642`, macOS often natively resolves `localhost` to its IPv6 address (`[::1]`). Since our Python HTTP server explicitly binds to `0.0.0.0` (IPv4), the tunnel drops connections with `Connection refused`. 
   - **The Fix**: Explicitly routing `cloudflared` to `http://127.0.0.1:8642`.

3. **Homebrew `ghcr.io` Networking**:
   When developing behind the Great Firewall, installing `cloudflared` via standard `Homebrew` often fails due to stalled connections to `ghcr.io` or unexpected Xcode license blocks.
   - **The Fix**: The installer uses direct binary fetch with `curl` proxy fallbacks, maintaining a completely isolated and portable `bin/` directory.
