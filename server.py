#!/usr/bin/env python3
"""
Markdown Bowser — A GitHub-style Markdown preview server.

Features:
  - Directory browsing with icons and breadcrumb navigation
  - Markdown rendering via mistune with GFM plugins
  - Code syntax highlighting via Pygments
  - Mobile-responsive layout
  - Multi-threaded HTTP server

Usage:
  python3 server.py [--host HOST] [--port PORT] [--root ROOT]
"""

import argparse
import base64
import html
import mimetypes
import os
import posixpath
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

import mistune
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8642
DEFAULT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Markdown renderer with Pygments code highlighting
# ---------------------------------------------------------------------------

class HighlightRenderer(mistune.HTMLRenderer):
    """Custom mistune renderer that applies Pygments syntax highlighting."""

    def block_code(self, code, info=None, **attrs):
        lang = None
        if info:
            lang = info.strip().split()[0]
        try:
            if lang:
                lexer = get_lexer_by_name(lang, stripall=True)
            else:
                lexer = guess_lexer(code)
        except Exception:
            lexer = TextLexer(stripall=True)
        formatter = HtmlFormatter(nowrap=False, cssclass="highlight")
        return highlight(code, lexer, formatter)


def _wrap_table(text):
    """Wrap table in a scrollable div for mobile responsiveness."""
    return '<div class="table-wrapper"><table>\n' + text + '</table></div>\n'


def create_markdown_parser():
    """Create a mistune Markdown parser with GFM-like plugins."""
    renderer = HighlightRenderer(escape=False)
    md = mistune.create_markdown(
        renderer=renderer,
        plugins=["strikethrough", "footnotes", "table", "task_lists"],
    )
    # Override the table render function registered by the plugin
    # to wrap tables in a scrollable div
    md.renderer.register('table', _wrap_table)
    return md


# ---------------------------------------------------------------------------
# Pygments CSS (github-dark inspired)
# ---------------------------------------------------------------------------

PYGMENTS_CSS = HtmlFormatter(style="github-dark").get_style_defs(".highlight")

# ---------------------------------------------------------------------------
# HTML Templates
# ---------------------------------------------------------------------------

PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>{title} — Markdown Bowser</title>
<style>
{css}
</style>
</head>
<body>
<div class="container">
  <nav class="breadcrumb">{breadcrumb}</nav>
  <main class="content">
{body}
  </main>
  <footer class="footer">Markdown Bowser · Powered by mistune + Pygments</footer>
</div>
</body>
</html>
"""

MAIN_CSS = r"""
/* ── Reset & Base ──────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0d1117;
  --surface: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --text-muted: #8b949e;
  --link: #58a6ff;
  --link-hover: #79c0ff;
  --accent: #238636;
  --code-bg: #1a1f29;
  --header-bg: #010409;
  --radius: 8px;
}

html { font-size: 16px; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
               Helvetica, Arial, sans-serif, "Apple Color Emoji";
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  -webkit-text-size-adjust: 100%;
}

/* ── Layout ────────────────────────────────────────────────── */
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px 24px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.content { flex: 1; }

/* ── Breadcrumb ────────────────────────────────────────────── */
.breadcrumb {
  padding: 12px 0;
  margin-bottom: 16px;
  font-size: 0.875rem;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
  word-break: break-all;
}
.breadcrumb a { color: var(--link); text-decoration: none; }
.breadcrumb a:hover { text-decoration: underline; }
.breadcrumb .sep { margin: 0 6px; opacity: 0.5; }

/* ── Footer ────────────────────────────────────────────────── */
.footer {
  margin-top: 48px;
  padding: 16px 0;
  border-top: 1px solid var(--border);
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ── Directory Listing ─────────────────────────────────────── */
.dir-list { list-style: none; }
.dir-list li {
  border-bottom: 1px solid var(--border);
}
.dir-list li:first-child { border-top: 1px solid var(--border); }
.dir-list a {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: var(--link);
  text-decoration: none;
  transition: background 0.15s;
  border-radius: var(--radius);
}
.dir-list a:hover { background: var(--surface); }
.dir-list .icon { font-size: 1.15rem; flex-shrink: 0; width: 24px; text-align: center; }
.dir-list .name { flex: 1; word-break: break-all; }
.dir-list .meta { font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; }

/* ── Markdown Body (GitHub-style) ──────────────────────────── */
.markdown-body h1, .markdown-body h2, .markdown-body h3,
.markdown-body h4, .markdown-body h5, .markdown-body h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  color: var(--text);
}
.markdown-body h1 { font-size: 2em; padding-bottom: 0.3em; border-bottom: 1px solid var(--border); }
.markdown-body h2 { font-size: 1.5em; padding-bottom: 0.3em; border-bottom: 1px solid var(--border); }
.markdown-body h3 { font-size: 1.25em; }
.markdown-body h4 { font-size: 1em; }

.markdown-body p { margin-top: 0; margin-bottom: 16px; }
.markdown-body a { color: var(--link); text-decoration: none; }
.markdown-body a:hover { text-decoration: underline; color: var(--link-hover); }

.markdown-body ul, .markdown-body ol {
  padding-left: 2em;
  margin-bottom: 16px;
}
.markdown-body li + li { margin-top: 4px; }

.markdown-body blockquote {
  margin: 0 0 16px;
  padding: 0 16px;
  color: var(--text-muted);
  border-left: 4px solid var(--border);
}

.markdown-body code {
  padding: 0.2em 0.4em;
  font-size: 85%;
  background: var(--code-bg);
  border-radius: 6px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}
.markdown-body pre {
  margin-bottom: 16px;
  padding: 16px;
  overflow-x: auto;
  border-radius: var(--radius);
  background: var(--code-bg);
  line-height: 1.45;
  -webkit-overflow-scrolling: touch;
}
.markdown-body pre code {
  padding: 0;
  background: transparent;
  font-size: 85%;
}

.markdown-body img {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius);
}

.markdown-body hr {
  height: 3px;
  margin: 24px 0;
  background: var(--border);
  border: 0;
  border-radius: 2px;
}

/* ── Tables ────────────────────────────────────────────────── */
.table-wrapper { overflow-x: auto; margin-bottom: 16px; -webkit-overflow-scrolling: touch; }
.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.9rem;
}
.markdown-body th, .markdown-body td {
  padding: 8px 16px;
  border: 1px solid var(--border);
}
.markdown-body th { background: var(--surface); font-weight: 600; }

/* ── Task Lists ────────────────────────────────────────────── */
.markdown-body .task-list-item { list-style: none; margin-left: -1.5em; }
.markdown-body .task-list-item input { margin-right: 6px; }

/* ── Highlight (Pygments) ──────────────────────────────────── */
.highlight { border-radius: var(--radius); overflow-x: auto; -webkit-overflow-scrolling: touch; }
.highlight pre { margin: 0; padding: 16px; background: var(--code-bg); }

/* ── Responsive ────────────────────────────────────────────── */
@media (max-width: 768px) {
  html { font-size: 15px; }
  .container { padding: 12px 16px; }
  .markdown-body pre { padding: 12px; font-size: 13px; }
  .markdown-body th, .markdown-body td { padding: 6px 10px; }
  .dir-list a { padding: 12px 8px; }
}

@media (max-width: 480px) {
  html { font-size: 14px; }
  .container { padding: 8px 12px; }
  .breadcrumb { font-size: 0.8rem; }
}
""" + "\n" + PYGMENTS_CSS


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def human_size(size_bytes):
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def file_icon(name, is_dir):
    """Return an emoji icon for a file or directory."""
    if is_dir:
        return "📁"
    ext = os.path.splitext(name)[1].lower()
    icons = {
        ".md": "📝", ".markdown": "📝", ".txt": "📄",
        ".py": "🐍", ".js": "🟨", ".ts": "🔷", ".jsx": "⚛️", ".tsx": "⚛️",
        ".html": "🌐", ".css": "🎨", ".json": "📋", ".yaml": "📋", ".yml": "📋",
        ".xml": "📋", ".toml": "📋",
        ".sh": "⚙️", ".bash": "⚙️", ".zsh": "⚙️",
        ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️",
        ".svg": "🖼️", ".webp": "🖼️",
        ".pdf": "📕", ".zip": "📦", ".tar": "📦", ".gz": "📦",
        ".mp4": "🎬", ".mov": "🎬", ".mp3": "🎵", ".wav": "🎵",
        ".go": "🔵", ".rs": "🦀", ".java": "☕", ".c": "🔧", ".cpp": "🔧",
        ".rb": "💎", ".swift": "🍊",
    }
    return icons.get(ext, "📄")


def build_breadcrumb(url_path):
    """Build HTML breadcrumb navigation from a URL path."""
    parts = [p for p in url_path.strip("/").split("/") if p]
    crumbs = ['<a href="/">🏠 Root</a>']
    accumulated = ""
    for part in parts:
        accumulated += "/" + part
        decoded = urllib.parse.unquote(part)
        crumbs.append(f'<a href="{accumulated}">{html.escape(decoded)}</a>')
    return '<span class="sep">/</span>'.join(crumbs)


# ---------------------------------------------------------------------------
# Request Handler
# ---------------------------------------------------------------------------

md_parser = create_markdown_parser()


class MarkdownHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with Markdown rendering and directory listing."""

    root_dir = DEFAULT_ROOT

    def translate_path(self, path):
        """Map URL path to filesystem path, restricted to root_dir."""
        path = urllib.parse.unquote(path.split("?", 1)[0].split("#", 1)[0])
        # Normalise and prevent path traversal
        path = posixpath.normpath(path)
        parts = path.split("/")
        result = self.root_dir
        for part in parts:
            if not part or part == ".":
                continue
            if part == "..":
                continue  # ignore parent references
            result = os.path.join(result, part)
        return result

    def check_auth(self):
        if getattr(self, 'auth_b64', None):
            auth_header = self.headers.get('Authorization')
            if auth_header != f"Basic {self.auth_b64}":
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Markdown Bowser"')
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"<h1>401 Unauthorized</h1><p>Please provide valid credentials.</p>")
                return False
        return True

    def do_HEAD(self):
        if not self.check_auth():
            return
        super().do_HEAD()

    def do_GET(self):
        if not self.check_auth():
            return

        fs_path = self.translate_path(self.path)

        # Security: must be inside an allowed root.
        real_path = os.path.realpath(fs_path)
        allowed = getattr(self, "allowed_roots", [os.path.realpath(self.root_dir)])
        if not any(os.path.commonpath([real_path, root]) == root for root in allowed):
            self.send_error(403, "Forbidden")
            return

        if os.path.isdir(real_path):
            # Redirect to trailing slash if missing
            if not self.path.endswith("/"):
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return
            self.serve_directory(real_path)
        elif os.path.isfile(real_path):
            if real_path.lower().endswith((".md", ".markdown")):
                self.serve_markdown(real_path)
            else:
                self.serve_static(real_path)
        else:
            self.send_error(404, "File not found")

    def serve_directory(self, dir_path):
        """Render a directory listing page."""
        url_path = self.path
        try:
            entries = os.listdir(dir_path)
        except PermissionError:
            self.send_error(403, "Permission denied")
            return

        # Separate dirs and files, sort each
        dirs = sorted(
            [e for e in entries if os.path.isdir(os.path.join(dir_path, e)) and not e.startswith(".")],
            key=str.lower,
        )
        files = sorted(
            [e for e in entries if os.path.isfile(os.path.join(dir_path, e)) and not e.startswith(".")],
            key=str.lower,
        )

        items_html = []

        # Parent directory link
        if url_path.strip("/"):
            parent = posixpath.dirname(url_path.rstrip("/")) + "/"
            items_html.append(
                f'<li><a href="{parent}">'
                '<span class="icon">⬆️</span>'
                '<span class="name">..</span>'
                "</a></li>"
            )

        for name in dirs:
            href = urllib.parse.quote(name, safe="") + "/"
            items_html.append(
                f'<li><a href="{href}">'
                f'<span class="icon">{file_icon(name, True)}</span>'
                f'<span class="name">{html.escape(name)}</span>'
                "</a></li>"
            )

        for name in files:
            href = urllib.parse.quote(name, safe="")
            full = os.path.join(dir_path, name)
            try:
                size = human_size(os.path.getsize(full))
            except OSError:
                size = ""
            items_html.append(
                f'<li><a href="{href}">'
                f'<span class="icon">{file_icon(name, False)}</span>'
                f'<span class="name">{html.escape(name)}</span>'
                f'<span class="meta">{size}</span>'
                "</a></li>"
            )

        body = '<ul class="dir-list">\n' + "\n".join(items_html) + "\n</ul>"
        title = urllib.parse.unquote(url_path) or "/"
        page = PAGE_TEMPLATE.format(
            title=html.escape(title),
            css=MAIN_CSS,
            breadcrumb=build_breadcrumb(url_path),
            body=body,
        )
        self.send_html(page)

    def serve_markdown(self, file_path):
        """Render a Markdown file as HTML."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
        except PermissionError:
            self.send_error(403, "Permission denied")
            return

        rendered = md_parser(raw)
        body = f'<article class="markdown-body">\n{rendered}\n</article>'
        title = os.path.basename(file_path)
        url_path = self.path
        page = PAGE_TEMPLATE.format(
            title=html.escape(title),
            css=MAIN_CSS,
            breadcrumb=build_breadcrumb(url_path),
            body=body,
        )
        self.send_html(page)

    def serve_static(self, file_path):
        """Serve a static file with the correct MIME type."""
        ctype, _ = mimetypes.guess_type(file_path)
        if ctype is None:
            ctype = "application/octet-stream"
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except PermissionError:
            self.send_error(403, "Permission denied")
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def send_html(self, html_content):
        """Send an HTML response."""
        data = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        """Override to include timestamp in log output."""
        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {self.address_string()} - {format % args}")


# ---------------------------------------------------------------------------
# Threaded HTTP Server
# ---------------------------------------------------------------------------

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server."""
    daemon_threads = True
    allow_reuse_address = True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Markdown Bowser — preview server")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Bind address (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"Root directory (default: {DEFAULT_ROOT})")
    parser.add_argument("--auth", default=None, help="Basic Auth credentials (format: user:password)")
    parser.add_argument("--allow", default=None, help="Additional allowed root paths (comma-separated)")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"Error: root directory does not exist: {root}")
        raise SystemExit(1)

    MarkdownHandler.root_dir = root
    MarkdownHandler.allowed_roots = [os.path.realpath(root)]
    if args.allow:
        for path in args.allow.split(","):
            path = path.strip()
            if path and os.path.isdir(path):
                MarkdownHandler.allowed_roots.append(os.path.realpath(path))
    if args.auth:
        MarkdownHandler.auth_b64 = base64.b64encode(args.auth.encode('utf-8')).decode('ascii')
    else:
        MarkdownHandler.auth_b64 = None

    server = ThreadedHTTPServer((args.host, args.port), MarkdownHandler)
    print(f"🚀 Markdown Bowser running at http://{args.host}:{args.port}")
    print(f"📂 Serving files from: {root}")
    print(f"📱 Mobile access: http://<your-lan-ip>:{args.port}")
    print("   Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
