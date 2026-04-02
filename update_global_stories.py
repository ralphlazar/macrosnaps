#!/usr/bin/env python3
"""
update_global_stories.py
========================
Refreshes global stories only. One Sonnet + web search call.
Writes directly to data.json — no draft file, no review gate.

Use mid-day when news is moving fast.

Usage:
    python3 update_global_stories.py

Next step:
    python3 build.py --apply

Requires:
    ANTHROPIC_API_KEY in .env
    data.json in the same folder
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
DATA_FILE    = "data.json"
TODAY        = date.today().isoformat()
MODEL_GLOBAL = "claude-sonnet-4-20250514"
LEVELS       = ["beginner", "moderate", "expert"]

STYLE_GUIDE = """
STORY WRITING RULES - apply to every story at every level:
- No em dashes or en dashes, ever. Use commas, periods, or parentheses instead.
- No passive voice where an active version is natural. "The Fed raised rates" not "rates were raised by the Fed."
- No hedging openers. Never start with "It is worth noting," "It is important to understand," or "This reflects the fact that."
- No AI-typical sentence starters. Do not begin consecutive sentences with "This metric," "This reflects," or "This suggests."
- Vary sentence length deliberately. Mix short punchy sentences with longer ones.
- Write numbers as real and specific. "Inflation hit 8.4%" not "the inflation rate stands at 8.4%."
- No filler conclusions. Never end with "overall," "in summary," or "taken together."
- No committee language. Write as if explaining to a smart friend, not presenting a report.
""".strip()


# ── Client ────────────────────────────────────────────────────────────────────
def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n  FATAL: ANTHROPIC_API_KEY not set. Add it to .env.\n")
        sys.exit(1)
    return anthropic.Anthropic(
        api_key=api_key,
        timeout=anthropic.Timeout(connect=30.0, read=180.0, write=30.0, pool=10.0)
    )


# ── JSON extractor ────────────────────────────────────────────────────────────
def extract_json(text):
    import re as _re
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
    if r: return r

    t = _re.sub(r",[ \t\n]*([]|}])", r"\1", text)
    t = t.replace("\u2018","'").replace("\u2019","'")
    t = t.replace("\u201c", chr(34)).replace("\u201d", chr(34))
    r = attempt(t)
    if r: return r

    def clean_string_value(m):
        inner = m.group(1)
        inner = inner.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        return chr(34) + inner + chr(34)
    t2 = _re.sub(r'"' + r'((?:[^"\\\n]|\\.)*)' + r'"', clean_string_value, t)
    r = attempt(t2)
    if r: return r

    raise ValueError(f"Could not parse JSON after repair attempts. Tail: ...{text[-200:]}")


# ── Strip citation tags leaked by web search ──────────────────────────────────
def clean_cite_tags(s):
    import re as _re
    if not isinstance(s, str):
        return s
    return _re.sub(r'</?antml:cite[^>]*>', '', s).strip()


# ── Global story prompt ───────────────────────────────────────────────────────
def build_global_system():
    return f"""You are a financial journalist writing the daily global macro briefing for MacroSnaps.

{STYLE_GUIDE}

Use web search to find today's most important macro and markets news. Then construct a single three-act narrative arc across three story cards:

CARD 1 - TODAY'S STORY: The dominant macro event of the day. The thing that matters most right now across markets or economies.

CARD 2 - BIGGEST MOVERS: Which markets, currencies, or economies are reacting, and how. Specific moves, specific places.

CARD 3 - THE CONNECTION: The "so what." What ties cards 1 and 2 together. What it means for the global picture going forward.

The three cards must tell one coherent story, not three unrelated headlines. A reader moving through all three should feel they understand not just what happened, but why it moved markets and what comes next.

All story text must be plain prose only. Never include HTML tags, <cite> tags, citation markup, markdown, or any other formatting. No angle brackets of any kind in story text.

Each card's content must be exactly 3 bullet points, not prose. Interpret, never describe. Answer: what is the story? What does it mean? What to watch next?

GOLDEN RULE: The reader can see the data. Do not describe it. Tell them what it means, why it matters, and what to watch.

Output ONLY a JSON object in this exact format with no preamble and no markdown fences:
{{
  "beginner": [
    {{"icon": "emoji", "label": "Short headline max 8 words", "bullets": ["bullet 1 (plain English, no jargon)", "bullet 2", "bullet 3"], "source": "Source name"}},
    {{"icon": "emoji", "label": "...", "bullets": ["...", "...", "..."], "source": "..."}},
    {{"icon": "emoji", "label": "...", "bullets": ["...", "...", "..."], "source": "..."}}
  ],
  "moderate": [
    {{"icon": "emoji", "label": "Short headline max 8 words", "bullets": ["bullet 1 (add one piece of context: historical, regional, or causal)", "bullet 2", "bullet 3"], "source": "Source name"}},
    {{"icon": "emoji", "label": "...", "bullets": ["...", "...", "..."], "source": "..."}},
    {{"icon": "emoji", "label": "...", "bullets": ["...", "...", "..."], "source": "..."}}
  ],
  "expert": [
    {{"icon": "emoji", "label": "Short headline max 8 words", "bullets": ["bullet 1 (specific numbers, directional signal)", "bullet 2", "bullet 3 (forward implication)"], "source": "Source name"}},
    {{"icon": "emoji", "label": "...", "bullets": ["...", "...", "..."], "source": "..."}},
    {{"icon": "emoji", "label": "...", "bullets": ["...", "...", "..."], "source": "..."}}
  ],
  "sources": [{{"title": "source name", "url": "https://..."}}]
}}

Card 1 is always Today's Story. Card 2 is always Biggest Movers. Card 3 is always The Connection. The icon and label must be the same across all three levels. Only the bullet depth changes. Each level must have exactly 3 bullets per card."""


def build_global_user():
    return f"Today is {TODAY}. Search for the three most important global macro and markets stories right now and write them at all three audience levels."


# ── Draft global stories ──────────────────────────────────────────────────────
def draft_global(client):
    print("  [GLOBAL] Fetching news + drafting global stories (Sonnet+search)...", end=" ", flush=True)

    messages = [{"role": "user", "content": build_global_user()}]
    sources  = []

    for turn in range(8):
        try:
            response = client.messages.create(
                model=MODEL_GLOBAL,
                max_tokens=5000,
                system=build_global_system(),
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=messages
            )
        except anthropic.RateLimitError:
            print("(rate limit, waiting 30s...)", end=" ", flush=True)
            time.sleep(30)
            continue

        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b.text for b in response.content if b.type == "text"]

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            text = "\n".join(text_blocks)
            parsed = extract_json(text)
            print("OK")
            return parsed, sources

        if tool_blocks:
            for tb in tool_blocks:
                sources.append({"query": tb.input.get("query", "")})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tb.id, "content": []}
                for tb in tool_blocks
            ]})
        else:
            text = "\n".join(text_blocks)
            parsed = extract_json(text)
            print("OK")
            return parsed, sources

    raise ValueError("Max turns reached without completing global stories")


# ── Apply directly to data.json ───────────────────────────────────────────────
def apply_global(parsed, sources, data):
    for lv in LEVELS:
        if lv not in parsed or len(parsed[lv]) < 3:
            raise ValueError(f"Missing or short level '{lv}' in global response")

    def _clean_cards(cards):
        return [{k: clean_cite_tags(v) if isinstance(v, str) else v
                 for k, v in c.items()} for c in cards]

    data["globalStories"] = {
        "beginner": _clean_cards(parsed["beginner"][:3]),
        "moderate": _clean_cards(parsed["moderate"][:3]),
        "expert":   _clean_cards(parsed["expert"][:3]),
        "sources":  parsed.get("sources", []) + [
            {"title": f"Web search: {s['query']}"} for s in sources if s.get("query")
        ]
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("  [GLOBAL] Applied to data.json.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(DATA_FILE):
        print(f"\n  FATAL: {DATA_FILE} not found.\n")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("\n" + "="*60)
    print("  MacroSnaps - Intraday Global Story Refresh")
    print(f"  {TODAY}  {datetime.now().strftime('%H:%M')}")
    print("="*60)

    client = get_client()
    t0 = time.time()

    try:
        parsed, sources = draft_global(client)
        apply_global(parsed, sources, data)
    except Exception as e:
        print(f"\n  FAILED: {e}\n")
        sys.exit(1)

    elapsed = int(time.time() - t0)
    print(f"\n  Done in {elapsed}s.")
    print(f"  Next step: python3 build.py --apply\n")


if __name__ == "__main__":
    main()
