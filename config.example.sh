#!/bin/bash
# ==========================================
# Markdown Bowser - User Configuration
# ==========================================
# IMPORTANT: Copy this file and rename it to `config.sh` before running.
# The `config.sh` file is ignored by Git to keep your credentials safe.

# 📂 The absolute path to the directory containing your Markdown notes.
# Example: export TARGET_ROOT="/Users/username/Documents/Notes"
export TARGET_ROOT="/path/to/your/markdown/directory"

# 🔒 HTTP Basic Auth credentials for securely accessing the preview web interface.
# Format: "username:password"
# Note: Anyone who clicks your Cloudflare Tunnel link will be prompted for this.
export AUTH_CREDS="admin:123456"
