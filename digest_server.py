#!/usr/bin/env python3
"""
digest_server.py — MacroSnaps Digest Web UI

Usage:
    python3 digest_server.py

Then open http://localhost:5000 in your browser.
"""

import json
import os
import subprocess
import sys
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).parent
DIGESTS_DIR = BASE_DIR / "digests"

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MacroSnaps · Digest</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f5f5f5;
    color: #1a1a1a;
    min-height: 100vh;
  }
  header {
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  header h1 { font-size: 18px; font-weight: 600; }
  header span { font-size: 13px; color: #888; }
  .container { max-width: 900px; margin: 0 auto; padding: 32px 24px; }

  /* Controls */
  .controls {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 24px;
    margin-bottom: 24px;
  }
  .controls h2 { font-size: 14px; font-weight: 600; color: #555; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em; }
  .mode-row { display: flex; gap: 10px; margin-bottom: 20px; }
  .mode-btn {
    flex: 1; padding: 12px; border: 1px solid #e0e0e0;
    border-radius: 8px; background: #fff; cursor: pointer;
    font-size: 14px; font-weight: 500; color: #444;
    transition: all 0.15s; text-align: center;
  }
  .mode-btn:hover { border-color: #aaa; background: #fafafa; }
  .mode-btn.active { border-color: #1a1a1a; background: #1a1a1a; color: #fff; }
  .generate-btn {
    width: 100%; padding: 13px; background: #1a1a1a;
    border: none; border-radius: 8px; color: #fff;
    font-size: 15px; font-weight: 600; cursor: pointer;
    transition: background 0.15s;
  }
  .generate-btn:hover { background: #333; }
  .generate-btn:disabled { background: #aaa; cursor: not-allowed; }

  /* Status */
  .status {
    display: none; align-items: center; gap: 10px;
    padding: 12px 16px; background: #fff;
    border: 1px solid #e0e0e0; border-radius: 8px;
    margin-bottom: 20px; font-size: 13px; color: #555;
  }
  .status.visible { display: flex; }
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid #e0e0e0; border-top-color: #1a1a1a;
    border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Output */
  .output {
    display: none; background: #fff;
    border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;
  }
  .output.visible { display: block; }
  .output-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 20px; border-bottom: 1px solid #e0e0e0;
    background: #fafafa;
  }
  .output-header-left { display: flex; align-items: center; gap: 10px; }
  .output-tag { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #888; }
  .output-date { font-size: 12px; color: #aaa; }
  .btn-row { display: flex; gap: 8px; }
  .action-btn {
    padding: 7px 14px; border-radius: 6px; font-size: 12px;
    font-weight: 600; cursor: pointer; transition: all 0.14s;
    font-family: inherit;
  }
  .copy-btn {
    background: #1a1a1a; border: 1px solid #1a1a1a; color: #fff;
  }
  .copy-btn:hover { background: #333; }
  .copy-btn.copied { background: #16a34a; border-color: #16a34a; }
  .toggle-btn {
    background: #fff; border: 1px solid #e0e0e0; color: #555;
  }
  .toggle-btn:hover { background: #f5f5f5; }

  /* Preview */
  .preview-pane { padding: 28px 32px; }
  .preview-pane.hidden { display: none; }
  .preview-pane .subject-block {
    font-size: 12px; color: #888; margin-bottom: 18px;
    padding: 10px 14px; background: #f5f5f5; border-radius: 6px;
  }
  .preview-pane .subject-block strong { color: #1a1a1a; font-size: 14px; display: block; margin-top: 4px; }
  .preview-body { font-size: 15px; line-height: 1.75; color: #1a1a1a; }
  .preview-body h1 { font-size: 22px; font-weight: 700; margin-bottom: 18px; line-height: 1.2; }
  .preview-body h2 { font-size: 16px; font-weight: 700; margin: 24px 0 8px; }
  .preview-body p { margin-bottom: 13px; }
  .preview-body a { color: #2563eb; text-decoration: underline; }
  .preview-body a:hover { color: #1d4ed8; }
  .preview-body ul { padding-left: 20px; margin-bottom: 13px; }
  .preview-body li { margin-bottom: 5px; }
  .preview-body hr { border: none; border-top: 1px solid #e0e0e0; margin: 22px 0; }
  .preview-body blockquote {
    border-left: 3px solid #e0e0e0; padding: 8px 16px;
    color: #666; font-style: italic; margin-bottom: 16px;
  }
  .preview-body strong { font-weight: 600; }

  /* Raw edit */
  .raw-pane { padding: 0; display: none; }
  .raw-pane.visible { display: block; }
  .raw-pane textarea {
    width: 100%; border: none; outline: none; resize: none;
    font-family: 'Menlo', 'Monaco', monospace; font-size: 13px;
    line-height: 1.7; color: #1a1a1a; padding: 24px 32px;
    min-height: 500px; background: #fff;
  }

  /* Error */
  .error {
    display: none; padding: 13px 17px; background: #fef2f2;
    border: 1px solid #fca5a5; border-radius: 8px;
    font-size: 13px; color: #dc2626; margin-top: 14px;
  }
  .error.visible { display: block; }
</style>
</head>
<body>

<header>
  <h1>MacroSnaps Digest</h1>
  <span id="headerDate"></span>
</header>

<div class="container">
  <div class="controls">
    <h2>Format</h2>
    <div class="mode-row">
      <button class="mode-btn active" data-mode="daily" onclick="setMode(this)">⚡ Daily Post</button>
      <button class="mode-btn" data-mode="weekly" onclick="setMode(this)">🌐 Weekly Digest</button>
      <button class="mode-btn" data-mode="notes" onclick="setMode(this)">✦ Substack Notes</button>
    </div>
    <button class="generate-btn" id="generateBtn" onclick="generate()">Generate digest</button>
    <div class="error" id="errorBox"></div>
  </div>

  <div class="status" id="statusBar">
    <div class="spinner"></div>
    <span id="statusText">Starting...</span>
  </div>

  <div class="output" id="outputPanel">
    <div class="output-header">
      <div class="output-header-left">
        <span class="output-tag" id="outputTag">DAILY</span>
        <span class="output-date" id="outputDate"></span>
      </div>
      <div class="btn-row">
        <button class="action-btn toggle-btn" onclick="toggleView()">Edit</button>
        <button class="action-btn copy-btn" id="copyBtn" onclick="copyText()">Copy</button>
      </div>
    </div>
    <div class="preview-pane" id="previewPane">
      <div id="subjectBlock"></div>
      <div class="preview-body" id="previewBody"></div>
    </div>
    <div class="raw-pane" id="rawPane">
      <textarea id="rawEditor" oninput="onEdit(this.value)"></textarea>
    </div>
  </div>
</div>

<script>
let currentMode = 'daily';
let rawMarkdown = '';
let showingEdit = false;

document.getElementById('headerDate').textContent = new Date().toLocaleDateString('en-GB', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
});

function setMode(btn) {
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentMode = btn.dataset.mode;
}

function setStatus(msg) {
  const bar = document.getElementById('statusBar');
  bar.classList.add('visible');
  document.getElementById('statusText').textContent = msg;
}

function hideStatus() {
  document.getElementById('statusBar').classList.remove('visible');
}

function showError(msg) {
  const el = document.getElementById('errorBox');
  el.textContent = msg;
  el.classList.add('visible');
}

function hideError() {
  document.getElementById('errorBox').classList.remove('visible');
}

async function generate() {
  hideError();
  const btn = document.getElementById('generateBtn');
  btn.disabled = true;
  btn.textContent = 'Generating...';
  setStatus('Running generate_digest.py...');
  document.getElementById('outputPanel').classList.remove('visible');

  try {
    const resp = await fetch(`/generate?mode=${currentMode}`);
    const data = await resp.json();

    if (!resp.ok || data.error) {
      throw new Error(data.error || 'Unknown error');
    }

    rawMarkdown = data.markdown;
    renderOutput(data.markdown, currentMode);
    document.getElementById('outputPanel').classList.add('visible');
    hideStatus();

  } catch (e) {
    hideStatus();
    showError('Error: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate digest';
  }
}

function mdToHtml(md) {
  let h = md;
  // Subject line
  h = h.replace(/^SUBJECT:\\s*(.+)$/m, (_, s) =>
    `<div id="subj-extracted" data-subject="${s.replace(/"/g,'&quot;')}"></div>`);
  h = h.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  h = h.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  h = h.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
  h = h.replace(/\\*(.+?)\\*/g, '<em>$1</em>');
  h = h.replace(/\\[([^\\]]+)\\]\\((https?:\\/\\/[^)]+)\\)/g,
    '<a href="$2" target="_blank" rel="noopener">$1</a>');
  h = h.replace(/^---$/gm, '<hr>');
  h = h.replace(/^- (.+)$/gm, '<li>$1</li>');
  h = h.replace(/(<li>.*<\\/li>\\n?)+/g, m => `<ul>${m}</ul>`);
  h = h.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  const lines = h.split('\\n');
  return lines.map(line => {
    const s = line.trim();
    if (!s) return '';
    if (s.startsWith('<')) return s;
    return `<p>${s}</p>`;
  }).join('\\n');
}

function renderOutput(md, mode) {
  const modeLabels = { daily: 'DAILY POST', weekly: 'WEEKLY DIGEST', notes: 'SUBSTACK NOTES' };
  document.getElementById('outputTag').textContent = modeLabels[mode] || mode.toUpperCase();
  document.getElementById('outputDate').textContent = new Date().toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric'
  });

  const html = mdToHtml(md);
  const bodyEl = document.getElementById('previewBody');
  bodyEl.innerHTML = html;

  // Extract and display subject line
  const subjEl = bodyEl.querySelector('#subj-extracted');
  const subjectBlock = document.getElementById('subjectBlock');
  if (subjEl) {
    const subj = subjEl.getAttribute('data-subject');
    subjectBlock.innerHTML = `<div class="subject-block">Subject line<strong>${subj}</strong></div>`;
    subjEl.remove();
  } else {
    subjectBlock.innerHTML = '';
  }

  document.getElementById('rawEditor').value = md;

  // Reset to preview view
  showingEdit = false;
  document.getElementById('previewPane').classList.remove('hidden');
  document.getElementById('rawPane').classList.remove('visible');
  document.querySelector('.toggle-btn').textContent = 'Edit';
}

function toggleView() {
  showingEdit = !showingEdit;
  const preview = document.getElementById('previewPane');
  const raw = document.getElementById('rawPane');
  const btn = document.querySelector('.toggle-btn');
  if (showingEdit) {
    preview.classList.add('hidden');
    raw.classList.add('visible');
    btn.textContent = 'Preview';
  } else {
    preview.classList.remove('hidden');
    raw.classList.remove('visible');
    btn.textContent = 'Edit';
  }
}

function onEdit(val) {
  rawMarkdown = val;
}

function copyText() {
  const text = document.getElementById('rawEditor').value;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('copyBtn');
    btn.textContent = 'Copied ✓';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'Copy';
      btn.classList.remove('copied');
    }, 2500);
  });
}
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default request logging
        pass

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())

        elif parsed.path == "/generate":
            params = parse_qs(parsed.query)
            mode = params.get("mode", ["daily"])[0]
            if mode not in ("daily", "weekly", "notes"):
                mode = "daily"

            self.run_generation(mode)

        else:
            self.send_response(404)
            self.end_headers()

    def run_generation(self, mode):
        try:
            print(f"  Generating {mode} digest...")
            result = subprocess.run(
                [sys.executable, str(BASE_DIR / "generate_digest.py"), "--mode", mode, "--no-browser"],
                capture_output=True,
                text=True,
                cwd=str(BASE_DIR),
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Script failed"
                self._json_response({"error": error_msg}, 500)
                return

            # Find the output file
            today = date.today().isoformat()
            # HTML file produced by generate_digest.py — extract markdown from it
            # Actually generate_digest writes .html — we need raw markdown
            # Look for the raw markdown file saved alongside
            md_path = DIGESTS_DIR / f"{today}-{mode}.md"
            html_path = DIGESTS_DIR / f"{today}-{mode}.html"

            markdown = ""
            if md_path.exists():
                with open(md_path) as f:
                    markdown = f.read()
            elif html_path.exists():
                # Parse markdown out of the textarea in the HTML
                with open(html_path) as f:
                    content = f.read()
                import re
                match = re.search(r'<textarea[^>]*>(.*?)</textarea>', content, re.DOTALL)
                if match:
                    markdown = match.group(1)
                    markdown = markdown.replace('&#96;', '`').replace('<\\/script>', '</script>')

            if not markdown:
                self._json_response({"error": "Could not find digest output"}, 500)
                return

            print(f"  Done: digests/{today}-{mode}.html")
            self._json_response({"markdown": markdown, "mode": mode})

        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    # Patch generate_digest.py to support --no-browser flag
    port = 8080
    server = HTTPServer(("localhost", port), Handler)

    print(f"\nMacroSnaps Digest Server")
    print(f"========================")
    print(f"  Open in browser: http://localhost:{port}")
    print(f"  Press Ctrl+C to stop\n")

    import webbrowser
    threading.Timer(0.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


if __name__ == "__main__":
    main()
