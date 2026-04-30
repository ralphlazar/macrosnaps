#!/usr/bin/env python3
"""
patch_remove_footer_substack_x.py

Removes from macrosnaps-shell.html:
  1. "Subscribe free" Substack button from footer
  2. X (Twitter) link + preceding separator from footer
  3. .footer-x-link CSS rules (now dead)

Educators button remains; .subscribe-btn CSS remains (Educators still uses it).
"""
import sys
from pathlib import Path

REPO = Path("/Users/lisaswerling/RALPH/AI/macrosnaps")
TARGET = REPO / "macrosnaps-shell.html"


def replace_unique(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    if count == 0:
        print(f"ERROR: {label} block not found in {TARGET.name}", file=sys.stderr)
        sys.exit(1)
    if count > 1:
        print(f"ERROR: {label} block found {count} times in {TARGET.name} (expected 1)", file=sys.stderr)
        sys.exit(1)
    return src.replace(old, new, 1)


def main():
    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found", file=sys.stderr)
        sys.exit(1)

    src = TARGET.read_text()
    original_len = len(src)

    # 1. Remove "Subscribe free" button. Keep Educators button.
    old_subscribe = (
        '    <a class="subscribe-btn" href="https://macrosnaps.substack.com" target="_blank" rel="noopener">Subscribe free</a>\n'
        '    <a class="subscribe-btn" href="/educators.html" target="_blank" rel="noopener">Educators</a>\n'
    )
    new_subscribe = (
        '    <a class="subscribe-btn" href="/educators.html" target="_blank" rel="noopener">Educators</a>\n'
    )
    src = replace_unique(src, old_subscribe, new_subscribe, "Subscribe button")

    # 2. Remove X link + preceding separator. Keep "Ping Me" as last item.
    old_x = (
        '    <span class="footer-link" data-ft="ping">Ping Me</span>\n'
        '    <span class="footer-sep">|</span>\n'
        '    <a href="https://x.com/macrosnapsapp" target="_blank" rel="noopener" class="footer-x-link" aria-label="MacroSnaps on X"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="11" height="11" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.737-8.835L1.254 2.25H8.08l4.253 5.622 5.91-5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>\n'
    )
    new_x = (
        '    <span class="footer-link" data-ft="ping">Ping Me</span>\n'
    )
    src = replace_unique(src, old_x, new_x, "X link")

    # 3. Remove dead .footer-x-link CSS rules.
    old_css = (
        '.footer-x-link{color:#555;display:inline-flex;align-items:center;padding:4px 2px;text-decoration:none;transition:color .2s}\n'
        '.footer-x-link:hover{color:var(--cyan)}\n'
    )
    src = replace_unique(src, old_css, '', ".footer-x-link CSS")

    TARGET.write_text(src)
    print(f"Patched {TARGET}")
    print(f"Bytes removed: {original_len - len(src)}")


if __name__ == "__main__":
    main()
