#!/usr/bin/env python3
"""
update_headlines.py
===================
Drafts fresh country-level stories and global stories.

Architecture (3 API calls total):
  Call 1 - Sonnet + web search: harvest recent data for all 12 countries.
            One call, compact JSON output. Feeds context into country batches.
  Call 2 - Haiku x3 batches: write country stories using recent data + forecast values.
            Recent data leads; forecasts passed as background context only.
  Call 3 - Sonnet + web search: top 3 global stories.
            Web search justified here because global stories need today's news.

Usage:
    python3 update_headlines.py                          # generate draft
    python3 update_headlines.py --apply                  # apply most recent approved file
    python3 update_headlines.py --apply stories_approved_2026-03-11.json

Requires:
    ANTHROPIC_API_KEY in .env
    data.json in the same folder
    pip3 install anthropic python-dotenv
"""

import json
import os
import sys
import time
import glob
import argparse
import re
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

# ── Config ───────────────────────────────────────────────────────────────────
DATA_FILE     = "data.json"
TODAY         = date.today().isoformat()
MODEL_COUNTRY = "claude-haiku-4-5-20251001"   # batch call, writing only
MODEL_GLOBAL  = "claude-sonnet-4-20250514"     # search-enabled, global stories
MODEL_SEARCH  = "claude-sonnet-4-20250514"     # search-enabled, recent data harvest
LEVELS        = ["beginner", "moderate", "expert"]

COUNTRY_ORDER = [
    "USA","CAN","GBR","JPN","DEU","FRA","ITA","CHN","IND","ZAF","BRA","RUS"
]

LEVEL_GUIDANCE = {
    "beginner": "3 short sentences. No jargon. What does this mean for an ordinary person?",
    "moderate": "3-4 sentences. Include one piece of context: a historical comparison, a regional comparison, or the key causal driver.",
    "expert":   "4-5 sentences. Specific numbers, a directional signal, and one forward-looking implication."
}

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


# ── Client ───────────────────────────────────────────────────────────────────
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
    # Strip markdown fences
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

    # Pass 1: straight
    r = attempt(text)
    if r: return r

    # Pass 2: trailing commas + smart quotes
    t = _re.sub(r",[ \t\n]*([]|}])", r"\1", text)
    t = t.replace("\u2018","'").replace("\u2019","'")
    t = t.replace("\u201c", chr(34)).replace("\u201d", chr(34))
    r = attempt(t)
    if r: return r

    # Pass 3: replace literal newlines/tabs inside JSON string values
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


# ── Build country batch prompt ────────────────────────────────────────────────
def build_batch_prompt(countries_data):
    """
    Single prompt containing all 12 countries' macro values.
    Returns the user message string.
    """
    lines = []
    lines.append(f"Today is {TODAY}.")
    lines.append("")
    lines.append("Write story bullets for each of the following 12 countries.")
    lines.append("Each country needs 3 bullets at each of 3 audience levels (beginner, moderate, expert).")
    lines.append("")
    lines.append(STYLE_GUIDE)
    lines.append("")
    lines.append("Level guidance:")
    for lv, guide in LEVEL_GUIDANCE.items():
        lines.append(f"  {lv}: {guide}")
    lines.append("")
    lines.append("Current macro metrics per country (use these as your factual anchors):")
    lines.append("")

    for code in COUNTRY_ORDER:
        cd = countries_data.get(code)
        if not cd:
            continue
        name = cd.get("name", code)
        macro = cd.get("metrics", {}).get("macro", {})
        lines.append(f"{code} - {name}")
        for k, v in macro.items():
            val = v.get("value") if isinstance(v, dict) else v
            lines.append(f"  {k}: {val}")
        lines.append("")

    lines.append("Output ONLY a JSON object in this exact structure with no preamble and no markdown fences:")
    lines.append("{")
    lines.append('  "USA": { "beginner": ["bullet","bullet","bullet"], "moderate": ["bullet","bullet","bullet"], "expert": ["bullet","bullet","bullet"] },')
    lines.append('  "CAN": { ... },')
    lines.append('  ... (all 12 country codes)')
    lines.append("}")
    lines.append("")
    lines.append("Use the exact 3-letter country codes as keys. Each level must have exactly 3 bullets. Each bullet is a single string of 1-3 sentences.")

    return "\n".join(lines)


# ── Build global prompt ───────────────────────────────────────────────────────
def build_global_system():
    return f"""You are a financial journalist writing the daily global macro briefing for MacroSnaps.

{STYLE_GUIDE}

Use web search to find today's most important macro and markets news. Then construct a single three-act narrative arc across three story cards:

CARD 1 - TODAY'S STORY: The dominant macro event of the day. The thing that matters most right now across markets or economies.

CARD 2 - BIGGEST MOVERS: Which markets, currencies, or economies are reacting, and how. Specific moves, specific places.

CARD 3 - THE CONNECTION: The "so what." What ties cards 1 and 2 together. What it means for the global picture going forward.

The three cards must tell one coherent story, not three unrelated headlines. A reader moving through all three should feel they understand not just what happened, but why it moved markets and what comes next.

All story text must be plain prose only. Never include HTML tags, <cite> tags, citation markup, markdown, or any other formatting. No angle brackets of any kind in story text.

Output ONLY a JSON object in this exact format with no preamble and no markdown fences:
{{
  "beginner": [
    {{"icon": "emoji", "label": "Short headline max 8 words", "body": "2-3 plain-English sentences.", "source": "Source name"}},
    {{"icon": "emoji", "label": "...", "body": "...", "source": "..."}},
    {{"icon": "emoji", "label": "...", "body": "...", "source": "..."}}
  ],
  "moderate": [
    {{"icon": "emoji", "label": "Short headline max 8 words", "body": "3-4 sentences with one piece of context.", "source": "Source name"}},
    {{"icon": "emoji", "label": "...", "body": "...", "source": "..."}},
    {{"icon": "emoji", "label": "...", "body": "...", "source": "..."}}
  ],
  "expert": [
    {{"icon": "emoji", "label": "Short headline max 8 words", "body": "4-5 sentences with specific numbers and a forward implication.", "source": "Source name"}},
    {{"icon": "emoji", "label": "...", "body": "...", "source": "..."}},
    {{"icon": "emoji", "label": "...", "body": "...", "source": "..."}}
  ],
  "sources": [{{"title": "source name", "url": "https://..."}}]
}}

Card 1 is always Today's Story. Card 2 is always Biggest Movers. Card 3 is always The Connection. The icon and label must be the same across all three levels. Only the body depth changes."""


def build_global_user():
    return f"Today is {TODAY}. Search for the three most important global macro and markets stories right now and write them at all three audience levels."


# ── Call 1: recent data harvest (Sonnet + web search) ────────────────────────
def fetch_recent_country_data(client, countries_data):
    """
    Single Sonnet + web search call that pulls recent macro data for all 12
    countries. Returns a dict keyed by country code with a short plain-text
    summary of the most recent data points (CPI print, GDP read, central bank
    decision, etc.). This feeds into the Haiku writing batches as lead context.
    """
    print("  [HARVEST] Fetching recent data for all 12 countries (Sonnet+search)...", end=" ", flush=True)

    country_list = []
    for code in COUNTRY_ORDER:
        cd = countries_data.get(code)
        if cd:
            country_list.append(f"{code} ({cd.get('name', code)})")

    system = (
        "You are a macro and markets researcher. Use web search to find what is "
        "happening right now for each of the listed economies. You may use up to 2 "
        "searches if needed. "
        "For each country, capture the most important thing happening today or this "
        "week. This includes: latest CPI or inflation print, latest GDP read, central "
        "bank decisions — but also geopolitical developments, trade policy changes, "
        "sanctions, conflicts, elections, political crises, or any other major event "
        "that is moving markets or affecting the economy. Prioritise what is most "
        "newsworthy, not just what has a data number. "
        "Include specific numbers and dates where available. "
        "Keep each country summary to 2-3 sentences. "
        "Output ONLY a JSON object with 3-letter country codes as keys and a single "
        "string value per country. No preamble, no markdown fences."
    )

    user = (
        f"Today is {TODAY}. Search for the latest macro, markets, and geopolitical "
        f"developments for these economies and write a short current summary for each:\n"
        + "\n".join(country_list)
        + "\n\nOutput format: {{\"USA\": \"current summary...\", \"CAN\": \"...\", ...}}"
    )

    messages = [{"role": "user", "content": user}]
    sources = []

    for turn in range(3):
        try:
            response = client.messages.create(
                model=MODEL_SEARCH,
                max_tokens=2000,
                system=system,
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
            return parsed

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
            return parsed

    print("FAILED (max turns)")
    return {}


# ── Call 2: country batch (Haiku, writing only) ───────────────────────────────
def draft_countries_batch(client, codes, countries_data, label, recent_data):
    """Draft stories for a subset of countries in one call."""
    print(f"  [COUNTRIES {label}] {', '.join(codes)}...", end=" ", flush=True)

    lines = []
    lines.append(f"Today is {TODAY}.")
    lines.append("")
    lines.append("Write story bullets for each of the following countries.")
    lines.append("Each country needs 3 bullets at each of 3 audience levels (beginner, moderate, expert).")
    lines.append("")
    lines.append(STYLE_GUIDE)
    lines.append("")
    lines.append("Level guidance:")
    for lv, guide in LEVEL_GUIDANCE.items():
        lines.append(f"  {lv}: {guide}")
    lines.append("")
    lines.append(
        "IMPORTANT: Lead each bullet with recent data and events, not with annual forecast numbers. "
        "Recent CPI prints, GDP reads, central bank decisions, and market moves are the story. "
        "Full-year forecast values are provided only as background context. Reference a forecast "
        "only if recent data is tracking meaningfully ahead of or behind it, and keep that "
        "reference brief (one clause, not the opening)."
    )
    lines.append("")
    lines.append("Recent data (lead with this):")
    lines.append("")
    for code in codes:
        recent = recent_data.get(code, "")
        if recent:
            lines.append(f"{code}: {recent}")
        else:
            lines.append(f"{code}: No recent data available. Use your knowledge of current conditions.")
    lines.append("")
    lines.append("Monthly actuals (verified recent prints - use these where harvest data is missing or vague):")
    lines.append("")
    for code in codes:
        cd = countries_data.get(code)
        if not cd:
            continue
        ma = cd.get("monthly_actuals", {})
        parts = []
        for series_key, label in [("inflation", "CPI"), ("unemployment", "Unemployment"), ("policy_rate", "Policy Rate")]:
            entries = ma.get(series_key, [])[:3]
            if entries:
                latest = entries[0]
                parts.append(f"{label} {latest['month']}: {latest['value']}%")
        lines.append(f"{code}: {', '.join(parts) if parts else 'no monthly actuals'}")
    lines.append("")
    lines.append("Full-year forecast values (background context only):")
    lines.append("")
    for code in codes:
        cd = countries_data.get(code)
        if not cd:
            continue
        name = cd.get("name", code)
        macro = cd.get("metrics", {}).get("macro", {})
        lines.append(f"{code} - {name}")
        for k, v in macro.items():
            val = v.get("value") if isinstance(v, dict) else v
            lines.append(f"  {k}: {val}")
        lines.append("")
    lines.append("BULLET COUNT RULE: EVERY level for EVERY country must have EXACTLY 3 bullets. Not 2, not 4. Exactly 3.")
    lines.append("If you run out of things to say, write a third bullet drawing on the forecast context.")
    lines.append("A response with any level containing fewer than 3 bullets is invalid.")
    lines.append("")
    lines.append("Output ONLY a JSON object with country codes as keys. No preamble, no markdown fences:")
    lines.append("{")
    lines.append('  "' + codes[0] + '": { "beginner": ["bullet","bullet","bullet"], "moderate": ["bullet","bullet","bullet"], "expert": ["bullet","bullet","bullet"] },')
    lines.append("  ... (one entry per country code listed above)")
    lines.append("}")
    lines.append("FINAL CHECK before outputting: count the bullets for every country and every level. Each must be exactly 3. Use straight apostrophes only.")

    user_prompt = "\n".join(lines)

    for attempt in range(2):
        response = client.messages.create(
            model=MODEL_COUNTRY,
            max_tokens=8000,
            messages=[{"role": "user", "content": user_prompt}]
        )
        text = response.content[0].text
        parsed = extract_json(text)

        # Validate bullet counts before accepting
        short = [
            f"{code}/{lv}"
            for code in codes
            if code in parsed
            for lv in LEVELS
            if not isinstance(parsed[code].get(lv), list) or len(parsed[code][lv]) < 3
        ]

        if not short:
            print("OK")
            return parsed

        if attempt == 0:
            print(f"(short bullets: {', '.join(short)}, retrying...)", end=" ", flush=True)
            time.sleep(5)
        else:
            raise ValueError(f"Batch {label} still short after retry: {', '.join(short)}")

    raise ValueError(f"Batch {label} failed validation")


def draft_countries(client, data):
    batch1 = COUNTRY_ORDER[:4]
    batch2 = COUNTRY_ORDER[4:8]
    batch3 = COUNTRY_ORDER[8:]
    countries_data = data.get("countries", {})
    recent_data = fetch_recent_country_data(client, countries_data)
    time.sleep(5)
    r1 = draft_countries_batch(client, batch1, countries_data, "1/3", recent_data)
    time.sleep(5)
    r2 = draft_countries_batch(client, batch2, countries_data, "2/3", recent_data)
    time.sleep(5)
    r3 = draft_countries_batch(client, batch3, countries_data, "3/3", recent_data)
    return {**r1, **r2, **r3}


# ── Call 3: global stories (Sonnet + web search) ──────────────────────────────
def draft_global(client):
    print("  [GLOBAL] Drafting global stories with web search (Sonnet)...", end=" ", flush=True)

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
                sources.append({"query": tb.input.get("query","")})
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


# ── Assemble draft ────────────────────────────────────────────────────────────
def generate_draft(client, data):
    draft = {
        "date": TODAY,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "countries": {},
        "globalStories": None,
        "_failures": []
    }

    # Call 1: global stories - run first to avoid Sonnet rate limit after harvest
    try:
        gs_parsed, gs_sources = draft_global(client)
        for lv in LEVELS:
            if lv not in gs_parsed or len(gs_parsed[lv]) < 3:
                raise ValueError(f"Missing or short level '{lv}' in global response")
        def _clean_cards(cards):
            return [{k: clean_cite_tags(v) if isinstance(v, str) else v for k, v in c.items()} for c in cards]
        draft["globalStories"] = {
            "beginner": _clean_cards(gs_parsed["beginner"][:3]),
            "moderate": _clean_cards(gs_parsed["moderate"][:3]),
            "expert":   _clean_cards(gs_parsed["expert"][:3]),
            "sources":  gs_parsed.get("sources", []) + [
                {"title": f"Web search: {s['query']}"} for s in gs_sources if s.get("query")
            ]
        }
    except KeyboardInterrupt:
        print("\n  Interrupted during global. Saving partial draft...")
        return draft
    except Exception as e:
        print(f"FAILED ({e})")
        draft["_failures"].append("GLOBAL")

    # Call 2: harvest + country batches
    try:
        country_results = draft_countries(client, data)
        for code in COUNTRY_ORDER:
            result = country_results.get(code)
            if not result:
                print(f"  [{code}] missing from batch response - flagged as failure")
                draft["_failures"].append(code)
                continue
            # Validate (belt-and-suspenders - batch already validates internally)
            ok = True
            for lv in LEVELS:
                if lv not in result or not isinstance(result[lv], list) or len(result[lv]) < 3:
                    print(f"  [{code}] bad structure for level '{lv}' - flagged as failure")
                    draft["_failures"].append(code)
                    ok = False
                    break
            if ok:
                draft["countries"][code] = {
                    "stories": {
                        "beginner": result["beginner"][:3],
                        "moderate": result["moderate"][:3],
                        "expert":   result["expert"][:3]
                    },
                    "sources": []
                }
    except KeyboardInterrupt:
        print("\n  Interrupted. Saving partial draft...")
    except Exception as e:
        print(f"FAILED ({e})")
        draft["_failures"].extend(COUNTRY_ORDER)

    return draft


# ── Save / apply ──────────────────────────────────────────────────────────────
def save_draft(draft):
    filename = f"stories_draft_{TODAY}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)
    return filename


def apply_draft(approved_file, data):
    print(f"\n  Reading approved draft: {approved_file}")
    with open(approved_file, "r", encoding="utf-8") as f:
        approved = json.load(f)

    applied_countries = []
    applied_global    = False

    for code, entry in approved.get("countries", {}).items():
        if code not in data.get("countries", {}):
            print(f"  [SKIP] {code} not in data.json")
            continue
        stories = entry.get("stories")
        if not stories:
            continue
        data["countries"][code]["stories"] = stories
        applied_countries.append(code)
        sources = entry.get("sources", [])
        if sources:
            print(f"  [{code}] Applied. Sources: {', '.join(s.get('title','?') for s in sources[:3])}")
        else:
            print(f"  [{code}] Applied.")

    gs = approved.get("globalStories")
    if gs:
        for lv in LEVELS:
            if lv in gs:
                data["globalStories"][lv] = gs[lv]
        applied_global = True
        sources = gs.get("sources", [])
        if sources:
            print(f"  [GLOBAL] Applied. Sources: {', '.join(s.get('title','?') for s in sources[:3])}")
        else:
            print(f"  [GLOBAL] Applied.")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n  Applied: {len(applied_countries)} countries" +
          (", global stories" if applied_global else ""))
    print(f"  data.json updated.")
    print(f"\n  Next step: python3 build.py\n")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", nargs="?", const="__latest__", metavar="FILE")
    args = parser.parse_args()

    if not os.path.exists(DATA_FILE):
        print(f"\n  FATAL: {DATA_FILE} not found.\n")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.apply is not None:
        if args.apply == "__latest__":
            candidates = sorted(glob.glob("stories_approved_*.json"), reverse=True)
            if not candidates:
                candidates = sorted(glob.glob("stories_draft_*.json"), reverse=True)
            if not candidates:
                print("\n  FATAL: No approved or draft file found.\n")
                sys.exit(1)
            approved_file = candidates[0]
        else:
            approved_file = args.apply
            if not os.path.exists(approved_file):
                print(f"\n  FATAL: File not found: {approved_file}\n")
                sys.exit(1)

        print("\n" + "="*60)
        print("  MacroSnaps - Apply Headlines")
        print("="*60)
        apply_draft(approved_file, data)
        return

    # Draft mode
    print("\n" + "="*60)
    print("  MacroSnaps - Draft Headlines")
    print(f"  {TODAY}")
    print("="*60)
    print(f"\n  3 API calls: Sonnet+search (harvest) + Haiku x3 (countries) + Sonnet+search (global)\n")

    client = get_client()
    t0     = time.time()
    draft  = generate_draft(client, data)
    elapsed = int(time.time() - t0)

    filename = save_draft(draft)

    total     = len(COUNTRY_ORDER) + 1
    succeeded = total - len(draft["_failures"])
    print(f"\n{'='*60}")
    print(f"  Done: {succeeded}/{total} in {elapsed}s")
    if draft["_failures"]:
        print(f"  Failures: {', '.join(draft['_failures'])}")
    print(f"  Saved: {filename}")
    print(f"\n  Next steps:")
    print(f"  1. Open headline_review.html and load {filename}")
    print(f"  2. Review, edit, approve, export stories_approved_{TODAY}.json")
    print(f"  3. python3 update_headlines.py --apply stories_approved_{TODAY}.json")
    print(f"  4. python3 build.py\n")


if __name__ == "__main__":
    main()
