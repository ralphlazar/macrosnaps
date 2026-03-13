#!/usr/bin/env python3
"""
update_commodity_stories.py
===========================
Checks all 9 commodity prices against the price when each story was last
written. Rewrites stories for any commodity that has moved beyond its
threshold. Applies changes directly to data.json with no review step.

Thresholds (hardcoded):
  Natural Gas: 10%
  Everything else: 5%

Usage:
    python3 update_commodity_stories.py

Requires:
    ANTHROPIC_API_KEY in .env
    data.json in the same folder
    pip3 install anthropic python-dotenv
"""

import json
import os
import sys
import time
from datetime import date, datetime

try:
    import anthropic
except ImportError:
    print("\n  FATAL: anthropic package not installed.")
    print("  Run: pip3 install anthropic python-dotenv\n")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Config ────────────────────────────────────────────────────────────────────
DATA_FILE = "data.json"
TODAY     = date.today().isoformat()
MODEL     = "claude-haiku-4-5-20251001"

# Movement threshold per symbol. Anything not listed defaults to 5%.
THRESHOLDS = {
    "NG": 0.10,   # Natural Gas - more volatile
}
DEFAULT_THRESHOLD = 0.05

STYLE_GUIDE = """
STORY WRITING RULES - apply to every story at every level:
- No em dashes or en dashes, ever. Use commas, periods, or parentheses instead.
- No passive voice where an active version is natural.
- No hedging openers. Never start with "It is worth noting" or "It is important to understand."
- No AI-typical sentence starters. Do not begin consecutive sentences with "This commodity" or "This reflects."
- Vary sentence length deliberately. Mix short punchy sentences with longer ones.
- Write numbers as real and specific. "Gold hit $3,200" not "gold prices are elevated."
- No filler conclusions. Never end with "overall," "in summary," or "taken together."
- No committee language. Write as if explaining to a smart friend, not presenting a report.
""".strip()

LEVEL_GUIDANCE = {
    "beginner": "2-3 sentences. What this commodity is and why its price matters to ordinary people.",
    "moderate": "3-4 sentences. Include one driver of the current price level and one downstream effect.",
    "expert":   "4-5 sentences. Include specific price, directional trend, supply/demand driver, and one forward implication.",
}


# ── Client ────────────────────────────────────────────────────────────────────
def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n  FATAL: ANTHROPIC_API_KEY not set. Add it to .env.\n")
        sys.exit(1)
    return anthropic.Anthropic(
        api_key=api_key,
        timeout=anthropic.Timeout(connect=30.0, read=120.0, write=30.0, pool=10.0)
    )


# ── JSON extractor ────────────────────────────────────────────────────────────
def extract_json(text):
    import re
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if part.startswith("json"):
                part = part[4:]
            part = part.strip()
            if part.startswith("{"):
                text = part
                break
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response")
    text = text[start:end]

    def attempt(s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    r = attempt(text)
    if r:
        return r

    t = re.sub(r",[ \t\n]*([\]}])", r"\1", text)
    t = t.replace("\u2018", "'").replace("\u2019", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    r = attempt(t)
    if r:
        return r

    raise ValueError(f"Could not parse JSON. Tail: ...{text[-200:]}")


# ── Drift check ───────────────────────────────────────────────────────────────
def check_drift(items):
    """
    Returns a list of items that need a story rewrite.
    An item with no storyWrittenAtPrice is always included (first-run bootstrap).
    """
    flagged = []
    for item in items:
        current_price = item.get("price")
        written_at    = item.get("storyWrittenAtPrice")
        symbol        = item.get("symbol", "")
        threshold     = THRESHOLDS.get(symbol, DEFAULT_THRESHOLD)

        if current_price is None:
            continue

        if written_at is None:
            flagged.append((item, "no prior price recorded (first run)"))
            continue

        if written_at == 0:
            flagged.append((item, "storyWrittenAtPrice is zero"))
            continue

        move = abs(current_price - written_at) / abs(written_at)
        if move >= threshold:
            pct = move * 100
            flagged.append((item, f"moved {pct:.1f}% vs {threshold*100:.0f}% threshold (was {written_at}, now {current_price})"))

    return flagged


# ── Draft stories ─────────────────────────────────────────────────────────────
def draft_stories(client, flagged_items):
    """
    Single Haiku call covering all flagged commodities.
    Returns a dict keyed by symbol: { beginner: "...", moderate: "...", expert: "..." }
    """
    lines = []
    lines.append(f"Today is {TODAY}.")
    lines.append("")
    lines.append("Write commodity stories for each of the following commodities.")
    lines.append("Each commodity needs one story at each of 3 audience levels: beginner, moderate, expert.")
    lines.append("")
    lines.append(STYLE_GUIDE)
    lines.append("")
    lines.append("Level guidance:")
    for lv, guide in LEVEL_GUIDANCE.items():
        lines.append(f"  {lv}: {guide}")
    lines.append("")
    lines.append("Commodities to write (current live prices):")
    lines.append("")

    for item, reason in flagged_items:
        lines.append(f"  {item['name']} ({item['symbol']})")
        lines.append(f"    Current price: {item['price']} {item['unit']}")
        lines.append(f"    YoY change: {item.get('change', 'n/a')}%")
        lines.append(f"    Category: {item.get('cat', 'n/a')}")
        lines.append("")

    lines.append("Output ONLY a JSON object keyed by symbol. Each value has beginner, moderate, and expert keys.")
    lines.append("Each value is a plain string (not an object, not a list). No preamble, no markdown fences.")
    lines.append("{")
    lines.append('  "CL": { "beginner": "story text", "moderate": "story text", "expert": "story text" },')
    lines.append("  ...")
    lines.append("}")

    prompt = "\n".join(lines)

    for attempt in range(2):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text
        parsed = extract_json(text)

        # Validate all symbols and levels present
        missing = []
        for item, _ in flagged_items:
            sym = item["symbol"]
            if sym not in parsed:
                missing.append(sym)
                continue
            for lv in ("beginner", "moderate", "expert"):
                if lv not in parsed[sym] or not parsed[sym][lv]:
                    missing.append(f"{sym}/{lv}")

        if not missing:
            return parsed

        if attempt == 0:
            print(f"  (missing: {', '.join(missing)}, retrying...)", end=" ", flush=True)
            time.sleep(5)
        else:
            raise ValueError(f"Still missing after retry: {', '.join(missing)}")

    raise ValueError("draft_stories failed after retries")


# ── Apply to data.json ────────────────────────────────────────────────────────
def apply_stories(data, flagged_items, new_stories):
    """
    Writes new stories and updates storyWrittenAtPrice in data.json.
    """
    applied = []
    for item, _ in flagged_items:
        sym = item["symbol"]
        if sym not in new_stories:
            print(f"  [{sym}] No story returned, skipping.")
            continue
        stories = new_stories[sym]
        item["story"] = {
            "beginner": stories["beginner"],
            "moderate": stories["moderate"],
            "expert":   stories["expert"],
        }
        item["storyWrittenAtPrice"] = item["price"]
        item["storyUpdatedDate"]    = TODAY
        applied.append(item["name"])

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return applied


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(DATA_FILE):
        print(f"\n  FATAL: {DATA_FILE} not found.\n")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("commodities", {}).get("items", [])
    if not items:
        print("\n  FATAL: No commodity items found in data.json.\n")
        sys.exit(1)

    print("\n" + "="*60)
    print("  MacroSnaps - Commodity Story Update")
    print(f"  {TODAY}")
    print("="*60 + "\n")

    # Check drift
    flagged = check_drift(items)

    if not flagged:
        print("  No commodity stories need updating today.\n")
        names = [item["name"] for item in items]
        print(f"  All within threshold: {', '.join(names)}\n")
        return

    print(f"  {len(flagged)} commodit{'y' if len(flagged) == 1 else 'ies'} flagged for rewrite:\n")
    for item, reason in flagged:
        print(f"  {item['name']:15s}  {reason}")
    print()

    # Draft
    client = get_client()
    print(f"  Drafting stories (Haiku)...", end=" ", flush=True)
    t0 = time.time()
    new_stories = draft_stories(client, flagged)
    elapsed = int(time.time() - t0)
    print(f"OK ({elapsed}s)\n")

    # Apply
    applied = apply_stories(data, flagged, new_stories)

    print(f"  Updated: {', '.join(applied)}")
    print(f"  data.json saved.")
    print(f"\n  Next step: python3 build.py\n")


if __name__ == "__main__":
    main()
