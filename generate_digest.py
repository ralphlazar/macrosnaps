#!/usr/bin/env python3
"""
generate_digest.py — MacroSnaps Substack digest generator

Usage:
    python3 generate_digest.py                  # daily post (default)
    python3 generate_digest.py --mode daily
    python3 generate_digest.py --mode weekly
    python3 generate_digest.py --mode notes

Reads data.json from the current directory.
Diffs against last snapshot to surface what changed.
Writes output to digests/YYYY-MM-DD-[mode].md
Saves a new snapshot to digests/snapshots/YYYY-MM-DD.json
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_JSON = BASE_DIR / "data.json"
DIGESTS_DIR = BASE_DIR / "digests"
SNAPSHOTS_DIR = DIGESTS_DIR / "snapshots"

DIGESTS_DIR.mkdir(exist_ok=True)
SNAPSHOTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MACRO_METRICS = [
    "GDP Growth",
    "Inflation",
    "Unemployment",
    "Budget Deficit",
    "Current Account",
    "Policy Rate",
]

MARKET_METRICS = [
    "Stock Market YTD",
    "Stock Market YTD (USD)",
    "10Y Bond Yield",
    "Yield Curve",
    "FX Rate",
]

COUNTRY_NAMES = {
    "USA": "United States",
    "CAN": "Canada",
    "GBR": "United Kingdom",
    "JPN": "Japan",
    "DEU": "Germany",
    "FRA": "France",
    "ITA": "Italy",
    "CHN": "China",
    "IND": "India",
    "ZAF": "South Africa",
    "BRA": "Brazil",
    "RUS": "Russia",
}

MACROSNAPS_URL = "https://macrosnaps.app"


# ---------------------------------------------------------------------------
# Load data.json
# ---------------------------------------------------------------------------
def load_data() -> dict:
    if not DATA_JSON.exists():
        print(f"✗ data.json not found at {DATA_JSON}")
        sys.exit(1)
    with open(DATA_JSON) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Snapshot: load previous, save current
# ---------------------------------------------------------------------------
def load_last_snapshot() -> dict:
    snapshots = sorted(SNAPSHOTS_DIR.glob("*.json"))
    if not snapshots:
        return {}
    with open(snapshots[-1]) as f:
        return json.load(f)


def save_snapshot(data: dict) -> None:
    today = date.today().isoformat()
    path = SNAPSHOTS_DIR / f"{today}.json"
    # Save a lean snapshot: just metric values and weather icons
    snapshot = {}
    for code, country in data.get("countries", {}).items():
        snapshot[code] = {"macro": {}, "market": {}}
        macro = country.get("metrics", {}).get("macro", {})
        for m in MACRO_METRICS:
            if m in macro:
                snapshot[code]["macro"][m] = macro[m].get("value", "")
        market = country.get("metrics", {}).get("market", {})
        for m in MARKET_METRICS:
            if m in market:
                raw = market[m]
                snapshot[code]["market"][m] = raw.get("value", "") if isinstance(raw, dict) else str(raw)
        # Commodities
    comm_snapshot = {}
    for item in data.get("commodities", {}).get("items", []):
        name = item.get("name", "")
        comm_snapshot[name] = item.get("price", "")
    snapshot["_commodities"] = comm_snapshot
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"  Snapshot saved: {path.name}")


# ---------------------------------------------------------------------------
# Delta detection
# ---------------------------------------------------------------------------
def detect_changes(data: dict, prev: dict) -> dict:
    """Compare current data.json against previous snapshot. Return structured delta."""
    changes = {
        "metric_changes": [],   # {country, metric, type, old, new}
        "stormy_flags": [],     # {country, metric, value} — stormy weather icon
        "market_moves": [],     # {country, metric, value}
        "commodity_moves": [],  # {name, price, change_pct}
        "new_stories": [],      # countries whose stories were updated today
    }

    today_str = date.today().isoformat()

    for code, country in data.get("countries", {}).items():
        name = COUNTRY_NAMES.get(code, code)
        macro = country.get("metrics", {}).get("macro", {})
        market = country.get("metrics", {}).get("market", {})
        prev_country = prev.get(code, {})

        # Macro metric changes
        for m in MACRO_METRICS:
            if m not in macro:
                continue
            current_val = macro[m].get("value", "")
            prev_val = prev_country.get("macro", {}).get(m, "")
            if prev_val and current_val != prev_val:
                changes["metric_changes"].append({
                    "country": name,
                    "code": code,
                    "metric": m,
                    "type": "macro",
                    "old": prev_val,
                    "new": current_val,
                })

        # Market metric changes
        for m in MARKET_METRICS:
            if m not in market:
                continue
            raw = market[m]
            current_val = raw.get("value", "") if isinstance(raw, dict) else str(raw)
            prev_val = prev_country.get("market", {}).get(m, "")
            if prev_val and current_val != prev_val:
                changes["market_moves"].append({
                    "country": name,
                    "code": code,
                    "metric": m,
                    "old": prev_val,
                    "new": current_val,
                })

        # Stormy flags — GDP Growth < 0% drives stormy icon per shell rule
        gdp = macro.get("GDP Growth", {})
        gdp_val = gdp.get("value", "")
        try:
            gdp_num = float(gdp_val.replace("%", "").strip())
            if gdp_num < 0:
                changes["stormy_flags"].append({
                    "country": name, "metric": "GDP Growth", "value": gdp_val
                })
        except (ValueError, AttributeError):
            pass

        # Also flag any metric with "stormy" in its story or value context
        for m in MACRO_METRICS:
            if m == "GDP Growth":
                continue
            story = macro.get(m, {}).get("story", {})
            # Flag if story was updated today
            last_updated = macro.get(m, {}).get("last_updated", "")
            if last_updated and last_updated.startswith(today_str):
                if name not in [x["country"] for x in changes["new_stories"]]:
                    changes["new_stories"].append({"country": name, "code": code})

        # Policy rate notable readings
        pol = macro.get("Policy Rate", {})
        pol_val = pol.get("value", "")
        try:
            pol_num = float(pol_val.replace("%", "").strip())
            if pol_num >= 10 or pol_num <= 0.25:
                changes["stormy_flags"].append({
                    "country": name, "metric": "Policy Rate", "value": pol_val
                })
        except (ValueError, AttributeError):
            pass

    # Commodity moves
    prev_comm = prev.get("_commodities", {})
    for item in data.get("commodities", {}).get("items", []):
        name = item.get("name", "")
        price = item.get("price", "")
        change = item.get("change", "")  # e.g. "+2.3%" or "-1.1%"
        prev_price = prev_comm.get(name, "")

        if change:
            try:
                chg_num = float(str(change).replace("%", "").replace("+", "").strip())
                if abs(chg_num) >= 1.5:  # flag moves >= 1.5%
                    changes["commodity_moves"].append({
                        "name": name,
                        "price": price,
                        "change": change,
                    })
            except (ValueError, AttributeError):
                pass
        elif prev_price and str(price) != str(prev_price):
            changes["commodity_moves"].append({
                "name": name, "price": price, "change": "moved"
            })

    return changes


# ---------------------------------------------------------------------------
# Build analytical brief for Claude
# ---------------------------------------------------------------------------
def build_brief(data: dict, changes: dict) -> str:
    today = date.today().strftime("%-d %B %Y")

    lines = [f"MacroSnaps data brief — {today}", ""]

    # Build date from _meta
    built_at = data.get("_meta", {}).get("generated", "today")
    lines.append(f"Data built: {built_at}")
    lines.append("")

    # Global stories
    global_stories = data.get("globalStories", {})
    if global_stories:
        lines.append("GLOBAL STORIES (moderate tier):")
        for tier_key in ["moderate"]:
            cards = global_stories.get(tier_key, [])
            for card in cards:
                label = card.get("label", "")
                body = card.get("body", "")
                lines.append(f"  [{label}] {body}")
        lines.append("")

    # What changed since last snapshot
    if changes["metric_changes"]:
        lines.append("MACRO METRIC CHANGES (since last digest):")
        for c in changes["metric_changes"]:
            lines.append(f"  {c['country']} {c['metric']}: {c['old']} -> {c['new']}")
        lines.append("")

    if changes["market_moves"]:
        lines.append("MARKET METRIC CHANGES (since last digest):")
        for c in changes["market_moves"]:
            lines.append(f"  {c['country']} {c['metric']}: {c['old']} -> {c['new']}")
        lines.append("")

    if changes["commodity_moves"]:
        lines.append("NOTABLE COMMODITY MOVES (>=1.5% daily):")
        for c in changes["commodity_moves"]:
            lines.append(f"  {c['name']}: {c['price']} ({c['change']})")
        lines.append("")

    if changes["stormy_flags"]:
        lines.append("STORMY FLAGS (negative or extreme readings):")
        for c in changes["stormy_flags"]:
            lines.append(f"  {c['country']} {c['metric']}: {c['value']}")
        lines.append("")

    if changes["new_stories"]:
        lines.append("STORIES UPDATED TODAY:")
        for c in changes["new_stories"]:
            lines.append(f"  {c['country']}")
        lines.append("")

    # Full current snapshot — all countries, all macro metrics
    lines.append("CURRENT MACRO READINGS (all countries):")
    for code, country in data.get("countries", {}).items():
        name = COUNTRY_NAMES.get(code, code)
        macro = country.get("metrics", {}).get("macro", {})
        market = country.get("metrics", {}).get("market", {})

        vals = []
        for m in MACRO_METRICS:
            v = macro.get(m, {}).get("value", "")
            if v:
                vals.append(f"{m}: {v}")

        # Add YTD stock
        ytd = market.get("Stock Market YTD", {})
        if not ytd:
            ytd = market.get("Stock Market YTD (USD)", {})
        if isinstance(ytd, dict):
            ytd_val = ytd.get("value", "")
        else:
            ytd_val = str(ytd) if ytd else ""
        if ytd_val:
            vals.append(f"Equities YTD: {ytd_val}")

        # Per-metric stories at moderate level
        story_lines = []
        for m in MACRO_METRICS:
            story = macro.get(m, {}).get("story", {})
            moderate = story.get("moderate", "")
            if moderate:
                story_lines.append(f"    {m}: {moderate}")

        lines.append(f"\n  {name} ({code}):")
        lines.append("    " + " | ".join(vals) if vals else "    (no data)")
        if story_lines:
            lines.append("  Stories:")
            lines.extend(story_lines)

    # Commodities
    lines.append("\nCURRENT COMMODITIES:")
    for item in data.get("commodities", {}).get("items", []):
        name = item.get("name", "")
        price = item.get("price", "")
        change = item.get("change", "")
        story = ""
        if isinstance(item.get("story"), dict):
            story = item["story"].get("moderate", item["story"].get("beginner", ""))
        elif isinstance(item.get("story"), str):
            story = item["story"]
        lines.append(f"  {name}: {price} ({change}) — {story}" if story else f"  {name}: {price} ({change})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mode prompts
# ---------------------------------------------------------------------------
MODE_INSTRUCTIONS = {
    "daily": """Write a ultra-short Substack daily post at moderate expertise level. Think: the site's country stories. One punchy sentence per idea, nothing wasted.

Structure:
SUBJECT: [one specific, compelling subject line. Not generic. No em-dashes.]

- [bullet 1: the single most important macro move or data point today]
- [bullet 2: second most important observation, different country or metric]
- [bullet 3: a tension, surprise, or thing to watch]
- [bullet 4: optional — only if genuinely noteworthy]

[Single CTA line: "Full picture across 12 economies: {url}"]

Rules:
- Each bullet is one sentence. Maximum 15 words per bullet.
- No em-dashes. No filler. No intro paragraph.
- First occurrence of jargon: hyperlink as [term]({url}).
- Total post: under 80 words.""",

    "weekly": """Write an ultra-short weekly macro digest for Substack at moderate expertise level. Scannable in 30 seconds.

Structure:
SUBJECT: [one specific, compelling subject line. No em-dashes.]

**What moved**
- [bullet: country/metric, what happened, why it matters — one sentence]
- [bullet: repeat for 2-3 more notable moves]

**What to watch**
- [bullet: specific event or data release next week]
- [bullet: second thing to watch]
- [bullet: third thing to watch]

[Single CTA line: "Track it live across 12 economies: {url}"]

Rules:
- Each bullet is one sentence. Maximum 15 words per bullet.
- No em-dashes. No intro paragraph. No filler.
- First occurrence of jargon: hyperlink as [term]({url}).
- Total post: under 150 words.""",

    "notes": """Write exactly 3 Substack Notes. Each is one sentence, punchy, standalone.

Format:
NOTE 1:
[text]

NOTE 2:
[text]

NOTE 3:
[text]

Rules:
- One sharp observation each: a data point, a tension, a surprise.
- One sentence per note. Under 25 words each.
- No em-dashes. No CTA. No jargon that needs explaining.
- Do not number the notes in the text itself.""",
}


def build_prompt(brief: str, mode: str) -> str:
    today = date.today().strftime("%-d %B %Y")
    instruction = MODE_INSTRUCTIONS[mode].replace("{url}", MACROSNAPS_URL)

    return f"""You are the editorial engine for MacroSnaps, a macro-economic briefing covering 12 countries. Today is {today}.

Your job: read the structured data brief below and write a Substack {mode} post. Do not summarise everything equally. Identify what actually matters today, what is surprising, what has changed, and lead with that.

{instruction}

STRICT WRITING RULES (no exceptions):
- Em-dashes are completely banned. Never use them. Use commas, colons, or parentheses instead.
- No AI-sounding phrases. Write like a sharp, informed human.
- No filler words: "notably", "importantly", "it is worth noting", "interestingly", "furthermore".
- No hedging: "it appears", "it seems", "one might argue".
- Every word must earn its place. If a sentence can be cut, cut it.
- Varied sentence openings. Never start two bullets the same way.
- Numbers and specifics over vague descriptions. "5%" not "significantly".

Output clean markdown only. No preamble, no "here is your post", no commentary after the post.

---
{brief}
"""


# ---------------------------------------------------------------------------
# Call Claude
# ---------------------------------------------------------------------------
def call_claude(prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("✗ ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    print("  Calling Claude API...")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
def markdown_to_html_preview(md: str) -> str:
    """Convert markdown to simple HTML for the preview pane."""
    import re
    html = md
    # Subject line — pull out and style specially
    html = re.sub(r'^SUBJECT:\s*(.+)$', r'<p class="subject-line"><span class="subject-label">Subject:</span> \1</p>', html, flags=re.MULTILINE)
    # Headers
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    # Links
    html = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html)
    # HR
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
    # Bullet points
    html = re.sub(r'^\- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*?</li>(\n|$))+', lambda m: '<ul>' + m.group(0) + '</ul>', html, flags=re.DOTALL)
    # Blockquote (intro placeholder)
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
    # Paragraphs — wrap blocks of text
    lines = html.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
        elif stripped.startswith('<'):
            result.append(stripped)
        else:
            result.append(f'<p>{stripped}</p>')
    return '\n'.join(result)


def write_output(content: str, mode: str) -> Path:
    import re as _re
    today = date.today().isoformat()
    today_pretty = date.today().strftime("%-d %B %Y")
    filename = f"{today}-{mode}.html"
    path = DIGESTS_DIR / filename

    mode_labels = {"daily": "Daily Post", "weekly": "Weekly Digest", "notes": "Substack Notes"}
    mode_label = mode_labels.get(mode, mode.title())

    # Extract subject line so it sits at top, before intro placeholder
    subj_match = _re.search(r'^SUBJECT:\s*(.+)$', content, _re.MULTILINE)
    subject_line = f"SUBJECT: {subj_match.group(1)}\n\n" if subj_match else ""
    body = _re.sub(r'^SUBJECT:\s*.+\n?\n?', '', content, flags=_re.MULTILINE).strip()

    if mode != "notes":
        full_markdown = subject_line + body + f"\n\n---\n[{MACROSNAPS_URL}]({MACROSNAPS_URL})"
    else:
        full_markdown = content

    preview_html = markdown_to_html_preview(full_markdown)

    # Escape markdown for the textarea
    escaped_markdown = full_markdown.replace('`', '&#96;').replace('</script>', '<\\/script>')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MacroSnaps · {mode_label} · {today_pretty}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=Instrument+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<style>
  :root {{
    --navy: #080d1a;
    --navy-2: #0d1525;
    --navy-3: #111d30;
    --cyan: #00e5ff;
    --cyan-dim: rgba(0,229,255,0.10);
    --border: rgba(0,229,255,0.18);
    --border-dim: rgba(255,255,255,0.07);
    --text: #c8d8e8;
    --text-dim: #6a7f96;
    --amber: #ffb347;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--navy);
    color: var(--text);
    font-family: 'Instrument Sans', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  /* Top bar */
  .topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 28px;
    background: var(--navy-2);
    border-bottom: 1px solid var(--border-dim);
    flex-shrink: 0;
  }}
  .topbar-left {{ display: flex; align-items: baseline; gap: 12px; }}
  .logo {{ font-family: 'DM Serif Display', serif; font-size: 20px; color: #fff; }}
  .logo span {{ color: var(--cyan); }}
  .badge {{
    font-family: 'DM Mono', monospace; font-size: 10px;
    color: var(--cyan); background: var(--cyan-dim);
    border: 1px solid var(--border); padding: 2px 8px;
    border-radius: 3px; letter-spacing: 0.08em; text-transform: uppercase;
  }}
  .topbar-right {{ display: flex; align-items: center; gap: 12px; }}
  .meta {{ font-size: 12px; color: var(--text-dim); }}
  .copy-btn {{
    background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(0,229,255,0.08));
    border: 1px solid var(--cyan); border-radius: 8px;
    padding: 9px 20px; color: var(--cyan);
    font-family: 'Instrument Sans', sans-serif;
    font-size: 14px; font-weight: 600; cursor: pointer;
    transition: all 0.18s; letter-spacing: 0.02em;
  }}
  .copy-btn:hover {{
    background: linear-gradient(135deg, rgba(0,229,255,0.25), rgba(0,229,255,0.15));
    box-shadow: 0 0 20px rgba(0,229,255,0.2);
  }}
  .copy-btn.copied {{ background: rgba(74,222,128,0.15); border-color: #4ade80; color: #4ade80; }}

  /* Main layout */
  .main {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    flex: 1;
    overflow: hidden;
    height: calc(100vh - 57px);
  }}

  /* Preview pane */
  .pane {{
    overflow-y: auto;
    padding: 36px 40px;
    border-right: 1px solid var(--border-dim);
  }}
  .pane-label {{
    font-family: 'DM Mono', monospace; font-size: 10px;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--text-dim); margin-bottom: 24px;
  }}

  /* Preview typography */
  .preview-body h1 {{
    font-family: 'DM Serif Display', serif;
    font-size: 26px; color: #fff; line-height: 1.2;
    margin-bottom: 20px; letter-spacing: -0.3px;
  }}
  .preview-body h2 {{
    font-family: 'DM Serif Display', serif;
    font-size: 18px; color: #fff; margin: 28px 0 10px;
  }}
  .preview-body p {{ margin-bottom: 14px; line-height: 1.75; font-size: 15px; }}
  .preview-body strong {{ color: #fff; font-weight: 600; }}
  .preview-body em {{ color: var(--amber); font-style: italic; }}
  .preview-body a {{ color: var(--cyan); text-decoration: none; }}
  .preview-body a:hover {{ text-decoration: underline; }}
  .preview-body hr {{ border: none; border-top: 1px solid var(--border-dim); margin: 24px 0; }}
  .preview-body ul {{ padding-left: 20px; margin-bottom: 14px; }}
  .preview-body li {{ margin-bottom: 6px; line-height: 1.7; font-size: 15px; }}
  .preview-body blockquote {{
    border-left: 3px solid var(--cyan); padding: 10px 16px;
    background: var(--cyan-dim); border-radius: 0 6px 6px 0;
    font-style: italic; color: var(--text-dim); margin-bottom: 20px;
    font-size: 14px; line-height: 1.6;
  }}
  .subject-line {{
    background: var(--navy-3); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 14px;
    font-size: 14px; margin-bottom: 24px;
  }}
  .subject-label {{
    font-family: 'DM Mono', monospace; font-size: 10px;
    color: var(--cyan); letter-spacing: 0.1em;
    text-transform: uppercase; margin-right: 8px;
  }}

  /* Edit pane */
  .edit-pane {{
    overflow-y: auto;
    padding: 36px 40px;
    display: flex;
    flex-direction: column;
  }}
  .edit-pane .pane-label {{ margin-bottom: 16px; }}
  .hint {{
    font-size: 12px; color: var(--text-dim);
    margin-bottom: 16px; line-height: 1.5;
  }}
  textarea {{
    flex: 1;
    width: 100%;
    min-height: calc(100vh - 200px);
    background: var(--navy-3);
    border: 1px solid var(--border-dim);
    border-radius: 8px;
    padding: 20px;
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    line-height: 1.75;
    resize: none;
    outline: none;
    transition: border-color 0.18s;
  }}
  textarea:focus {{ border-color: var(--cyan); }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <div class="logo">Macro<span>Snaps</span></div>
    <div class="badge">{mode_label}</div>
    <span class="meta">{today_pretty}</span>
  </div>
  <div class="topbar-right">
    <span class="meta">Edit on the right · Copy · Paste into Substack</span>
    <button class="copy-btn" onclick="copyText()">Copy to clipboard</button>
  </div>
</div>

<div class="main">
  <div class="pane">
    <div class="pane-label">Preview</div>
    <div class="preview-body" id="preview">
      {preview_html}
    </div>
  </div>

  <div class="edit-pane">
    <div class="pane-label">Edit</div>
    <p class="hint">Edit the text below, then hit Copy. Paste directly into Substack.</p>
    <textarea id="editor" oninput="updatePreview(this.value)">{escaped_markdown}</textarea>
  </div>
</div>

<script>
// Simple markdown -> HTML for live preview
function mdToHtml(md) {{
  let h = md;
  h = h.replace(/^SUBJECT:\\s*(.+)$/gm, '<p class="subject-line"><span class="subject-label">Subject:</span> $1</p>');
  h = h.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  h = h.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  h = h.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
  h = h.replace(/\\*(.+?)\\*/g, '<em>$1</em>');
  h = h.replace(/\\[([^\\]]+)\\]\\((https?:\\/\\/[^)]+)\\)/g, '<a href="$2" target="_blank">$1</a>');
  h = h.replace(/^---$/gm, '<hr>');
  h = h.replace(/^- (.+)$/gm, '<li>$1</li>');
  h = h.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  const lines = h.split('\\n');
  return lines.map(line => {{
    const s = line.trim();
    if (!s) return '<br>';
    if (s.startsWith('<')) return s;
    return '<p>' + s + '</p>';
  }}).join('\\n');
}}

function updatePreview(val) {{
  document.getElementById('preview').innerHTML = mdToHtml(val);
}}

function copyText() {{
  const text = document.getElementById('editor').value;
  navigator.clipboard.writeText(text).then(() => {{
    const btn = document.querySelector('.copy-btn');
    btn.textContent = 'Copied ✓';
    btn.classList.add('copied');
    setTimeout(() => {{
      btn.textContent = 'Copy to clipboard';
      btn.classList.remove('copied');
    }}, 2500);
  }});
}}
</script>
</body>
</html>"""

    with open(path, "w") as f:
        f.write(html)

    # Save raw markdown for digest_server.py
    md_path = DIGESTS_DIR / f"{today}-{mode}.md"
    with open(md_path, "w") as f:
        f.write(full_markdown)

    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import webbrowser

    parser = argparse.ArgumentParser(description="MacroSnaps Substack digest generator")
    parser.add_argument(
        "--mode",
        choices=["daily", "weekly", "notes"],
        default="daily",
        help="Digest format (default: daily)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Skip opening browser (used when called from digest_server.py)",
    )
    args = parser.parse_args()
    mode = args.mode

    print(f"\nMacroSnaps Digest Generator — {mode.upper()}")
    print(f"{'=' * 42}")

    print("  Loading data.json...")
    data = load_data()
    built_at = data.get("_meta", {}).get("generated", "unknown")
    print(f"  Data built: {built_at}")

    print("  Loading last snapshot...")
    prev = load_last_snapshot()
    if prev:
        print(f"  Previous snapshot found: {sorted(SNAPSHOTS_DIR.glob('*.json'))[-1].name}")
    else:
        print("  No previous snapshot — first run, no delta available")

    print("  Detecting changes...")
    changes = detect_changes(data, prev)

    n_changes = len(changes["metric_changes"]) + len(changes["market_moves"])
    n_stormy = len(changes["stormy_flags"])
    n_comms = len(changes["commodity_moves"])
    print(f"  {n_changes} metric change(s), {n_stormy} stormy flag(s), {n_comms} notable commodity move(s)")

    print("  Building analytical brief...")
    brief = build_brief(data, changes)

    prompt = build_prompt(brief, mode)

    content = call_claude(prompt)

    print("  Saving snapshot...")
    save_snapshot(data)

    print("  Writing digest...")
    output_path = write_output(content, mode)

    print(f"\n✓ Done — opening in browser.")
    print(f"  Edit on the right, hit Copy, paste into Substack.\n")

    if not args.no_browser:
        webbrowser.open(output_path.as_uri())


if __name__ == "__main__":
    main()
