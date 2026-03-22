#!/usr/bin/env python3
"""
digest_server.py - MacroSnaps Digest Web UI
Usage: python3 digest_server.py
Then open http://localhost:8080
"""

import json
import os
import re
import subprocess
import sys
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).parent
DIGESTS_DIR = BASE_DIR / "digests"
UI_FILE = BASE_DIR / "digest_ui.html"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            if not UI_FILE.exists():
                self._text_response("digest_ui.html not found in macrosnaps folder", 500)
                return
            with open(UI_FILE, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/generate":
            params = parse_qs(parsed.query)
            mode = params.get("mode", ["daily"])[0]
            if mode not in ("daily", "weekly", "notes", "linkedin"):
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

            today = date.today().isoformat()
            md_path = DIGESTS_DIR / f"{today}-{mode}.md"

            if not md_path.exists():
                self._json_response({"error": f"Output file not found: {md_path.name}"}, 500)
                return

            with open(md_path) as f:
                markdown = f.read()

            print(f"  Done: digests/{today}-{mode}.md")

            tweets = self.generate_tweets(markdown)
            linkedin = self.generate_linkedin(markdown) if mode == "weekly" else None

            self._json_response({
                "markdown": markdown,
                "mode": mode,
                "tweets": tweets,
                "linkedin": linkedin,
            })

        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def generate_tweets(self, markdown):
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return []
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            body = re.sub(r"^SUBJECT:.*$", "", markdown, flags=re.MULTILINE).strip()
            prompt = (
                "You are writing tweets for @MacroSnapsApp, a macro-economic briefing covering 12 economies.\n\n"
                "From the digest below, write exactly 3 tweets. Each tweet must:\n"
                "- The text before the URL must be 256 characters or fewer (Twitter wraps all URLs to 23 chars, so 256 + space + URL = 280 exactly)\n"
                "- Be a single sharp observation: one data point, one tension, one surprise\n"
                "- End with the bare URL: macrosnaps.app\n"
                "- No markdown links, no [text](url) formatting, no HTML links. Bare URL only.\n"
                "- No em-dashes. No hashtags. No filler.\n"
                "- Sound like a sharp human, not a bot.\n\n"
                "Output exactly this format, nothing else:\n"
                "TWEET1: [text] macrosnaps.app\n"
                "TWEET2: [text] macrosnaps.app\n"
                "TWEET3: [text] macrosnaps.app\n\n"
                f"Digest:\n{body[:1500]}"
            )
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = msg.content[0].text
            tweets = []
            for line in raw.split("\n"):
                for prefix in ["TWEET1:", "TWEET2:", "TWEET3:"]:
                    if line.startswith(prefix):
                        tweets.append(line[len(prefix):].strip())
            return tweets[:3]
        except Exception as e:
            print(f"  Tweet generation failed: {e}")
            return []

    def generate_linkedin(self, markdown):
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return ""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            body = re.sub(r"^SUBJECT:.*$", "", markdown, flags=re.MULTILINE).strip()
            prompt = (
                "You are writing a LinkedIn post for Ralph Lazar, creator of MacroSnaps (macrosnaps.app), "
                "a macro-economic briefing covering 12 economies.\n\n"
                "From the weekly digest below, write one LinkedIn post. Rules:\n"
                "- Under 120 words total.\n"
                "- Open with one line of personal context in Ralph's voice. A real human observation.\n"
                "- 3-4 bullet points with the week's most important macro moves. Specific numbers.\n"
                "- One forward-looking closing line.\n"
                "- End with: Full picture across 12 economies: macrosnaps.app\n"
                "- No em-dashes. Maximum 2 hashtags at the very end, or none.\n"
                "- No markdown links. LinkedIn does not render them. Bare URLs only.\n"
                "- Warm but authoritative. Never use: notably, importantly, it is worth noting.\n"
                "- Output the post only. No preamble.\n\n"
                f"Weekly digest:\n{body[:2000]}"
            )
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text.strip()
        except Exception as e:
            print(f"  LinkedIn generation failed: {e}")
            return ""

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text_response(self, text, status=200):
        body = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
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
