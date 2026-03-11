#!/usr/bin/env python3
"""
MacroSnaps update_stories.py
============================
Diffs data.json against the last git commit, identifies metrics whose
values changed, calls the Claude API to rewrite stories for those metrics,
and writes the results back into data.json.

Usage:
    python3 update_stories.py             - run normally
    python3 update_stories.py --dry-run   - show what would change, no API calls, no writes
    python3 update_stories.py --force-all - rewrite every metric regardless of changes

Requires:
    ANTHROPIC_API_KEY in .env (same folder as this script)
    pip3 install anthropic python-dotenv --break-system-packages
"""

import json
import os
import sys
import subprocess
import argparse
from datetime import date
from dotenv import load_dotenv
import anthropic

# ── Config ───────────────────────────────────────────────────────────────────

DATA_FILE = "data.json"
TODAY = date.today().isoformat()
MODEL = "claude-sonnet-4-20250514"

# These 4 metrics have no reliable free data source and display as "not available".
# Stories are skipped while values remain void. If a paid source is added post-launch
# and values start appearing, the script will detect the change and rewrite normally.
DATA_VOID_METRICS = {"Equity Vol", "Corp Spread", "Sov CDS", "FX Vol"}

# FX metric key per country (varies)
FX_KEYS = {
    "USA": "USD/DXY", "CAN": "CAD/USD", "GBR": "GBP/USD", "JPN": "USD/JPY",
    "DEU": "EUR/USD", "FRA": "EUR/USD", "ITA": "EUR/USD", "CHN": "USD/CNY",
    "IND": "USD/INR", "ZAF": "USD/ZAR", "BRA": "USD/BRL", "RUS": "USD/RUB"
}

STORY_LEVELS = ["beginner", "moderate", "expert"]

# ── Style guide (included verbatim in every Claude API call) ──────────────────

STYLE_GUIDE = """
Story writing style rules - apply every one of these to every story at every level:

- No em dashes or en dashes, ever. Use commas, periods, or parentheses instead.
- No passive voice where an active version is natural. "The Fed raised rates" not "rates were raised by the Fed."
- No hedging openers. Never start a sentence with "It is worth noting," "It is important to understand," or "This reflects the fact that."
- No AI-typical sentence starters. Do not begin consecutive sentences with "This metric," "This reflects," or "This suggests."
- Vary sentence length deliberately. Mix short punchy sentences with longer ones. Uniform sentence length is a tell.
- Write numbers as if they are real and specific. "Inflation hit 8.4%" reads better than "the inflation rate stands at 8.4%."
- No filler conclusions. Never end a story with "overall," "in summary," or "taken together."
- No committee language. Write as if explaining to a smart friend, not presenting a report.
- Before outputting any story, scan it against every rule above and rewrite any sentence that fails. Output only the final corrected version.

Audience levels:
- beginner: 2-3 plain-English sentences. No jargon. Anyone can follow it.
- moderate: 3-4 sentences. Use standard financial terms but explain implications clearly.
- expert: 4-5 sentences. Use technical language freely. Reference specific data, mechanisms, and market implications.
""".strip()


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_env():
    """Load .env from the script's directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    load_dotenv(env_path)
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        print("\n  FATAL: ANTHROPIC_API_KEY not found in .env file.")
        print("  Add this line to your .env file:")
        print("  ANTHROPIC_API_KEY=sk-ant-your-key-here\n")
        sys.exit(1)
    return key


def get_committed_data():
    """Return data.json from the last git commit as a dict, or None if unavailable."""
    result = subprocess.run(
        ["git", "show", "HEAD:data.json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def value_changed(new_val, old_val):
    """Return True if the metric value changed meaningfully."""
    return str(new_val).strip() != str(old_val).strip()


def find_changed_metrics(current, committed):
    """
    Compare current data.json against committed version.
    Returns a list of dicts describing each metric that changed.
    Each dict has: type, country (or commodity name), section, metric, old_value, new_value.
    """
    changed = []

    # Per-country metrics
    for code, country in current.get("countries", {}).items():
        old_country = committed.get("countries", {}).get(code, {})
        for section in ["macro", "market"]:
            new_group = country.get("metrics", {}).get(section, {})
            old_group = old_country.get("metrics", {}).get(section, {})
            for metric_name, new_entry in new_group.items():
                if not isinstance(new_entry, dict):
                    continue
                new_val = new_entry.get("value")
                old_entry = old_group.get(metric_name, {})
                old_val = old_entry.get("value") if isinstance(old_entry, dict) else old_entry
                if value_changed(new_val, old_val):
                    changed.append({
                        "type": "metric",
                        "code": code,
                        "country_name": country.get("name", code),
                        "section": section,
                        "metric": metric_name,
                        "old_value": old_val,
                        "new_value": new_val,
                        "tier": new_entry.get("tier", "daily"),
                    })

    # Commodities
    new_comms = {i["name"]: i for i in current.get("commodities", {}).get("items", [])}
    old_comms = {i["name"]: i for i in committed.get("commodities", {}).get("items", [])}
    for name, new_item in new_comms.items():
        old_item = old_comms.get(name, {})
        if value_changed(new_item.get("price"), old_item.get("price")):
            changed.append({
                "type": "commodity",
                "name": name,
                "unit": new_item.get("unit", ""),
                "old_value": old_item.get("price"),
                "new_value": new_item.get("price"),
            })

    return changed


def all_metrics(current):
    """
    Return every rewritable metric (for --force-all mode).
    Same structure as find_changed_metrics but includes everything.
    """
    items = []

    for code, country in current.get("countries", {}).items():
        for section in ["macro", "market"]:
            group = country.get("metrics", {}).get(section, {})
            for metric_name, entry in group.items():
                if not isinstance(entry, dict):
                    continue
                items.append({
                    "type": "metric",
                    "code": code,
                    "country_name": country.get("name", code),
                    "section": section,
                    "metric": metric_name,
                    "old_value": None,
                    "new_value": entry.get("value"),
                    "tier": entry.get("tier", "daily"),
                })

    for item in current.get("commodities", {}).get("items", []):
        items.append({
            "type": "commodity",
            "name": item["name"],
            "unit": item.get("unit", ""),
            "old_value": None,
            "new_value": item.get("price"),
        })

    return items


# ── Claude API calls ──────────────────────────────────────────────────────────

def call_claude_metric(client, item):
    """
    Call Claude to rewrite stories for a single country metric.
    Returns a dict with beginner, moderate, expert keys (plain strings).
    """
    change_desc = (
        f"The value changed from {item['old_value']} to {item['new_value']}."
        if item["old_value"] is not None
        else f"The current value is {item['new_value']}."
    )

    prompt = f"""You are writing metric stories for MacroSnaps, a global macro dashboard.

Country: {item['country_name']} ({item['code']})
Metric: {item['metric']}
Section: {item['section']}
{change_desc}

Write three story variants for this metric at the value shown above.

{STYLE_GUIDE}

Respond ONLY with valid JSON. No preamble, no markdown fences. Example format:
{{"beginner": "...", "moderate": "...", "expert": "..."}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def call_claude_commodity(client, item):
    """
    Call Claude to rewrite stories for a commodity.
    Returns a dict with beginner, moderate, expert keys (plain strings).
    """
    change_desc = (
        f"The price changed from {item['old_value']} to {item['new_value']} {item['unit']}."
        if item["old_value"] is not None
        else f"The current price is {item['new_value']} {item['unit']}."
    )

    prompt = f"""You are writing commodity price stories for MacroSnaps, a global macro dashboard.

Commodity: {item['name']}
Unit: {item['unit']}
{change_desc}

Write three story variants for this commodity at the price shown above.

{STYLE_GUIDE}

Respond ONLY with valid JSON. No preamble, no markdown fences. Example format:
{{"beginner": "...", "moderate": "...", "expert": "..."}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


# ── Write results back into data ──────────────────────────────────────────────

def write_metric_story(data, item, stories):
    """Write beginner/moderate/expert strings into the metric's story field."""
    entry = (
        data["countries"][item["code"]]["metrics"]
        [item["section"]][item["metric"]]
    )
    entry["story"] = {
        "beginner": stories["beginner"],
        "moderate": stories["moderate"],
        "expert": stories["expert"],
    }
    entry["last_updated"] = TODAY


def write_commodity_story(data, item, stories):
    """
    Write beginner/moderate/expert into commodity story.
    Commodity stories use {text: "..."} dicts per level.
    """
    comm_items = data["commodities"]["items"]
    for comm in comm_items:
        if comm["name"] == item["name"]:
            comm["story"] = {
                "beginner": {"text": stories["beginner"]},
                "moderate": {"text": stories["moderate"]},
                "expert":   {"text": stories["expert"]},
            }
            return


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MacroSnaps story updater")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Show what would be rewritten without calling the API or writing anything")
    parser.add_argument("--force-all", action="store_true",
                        help="Rewrite every metric regardless of value changes")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  MacroSnaps update_stories.py")
    print(f"  {TODAY}")
    if args.dry_run:
        print("  MODE: DRY RUN - no API calls, no writes")
    elif args.force_all:
        print("  MODE: FORCE ALL - rewriting every metric")
    print("="*60)

    # Load API key
    api_key = load_env()
    client = anthropic.Anthropic(api_key=api_key)

    # Load current data.json
    if not os.path.exists(DATA_FILE):
        print(f"\n  FATAL: {DATA_FILE} not found. Run from ~/Downloads/macrosnaps/.\n")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Find what to rewrite
    if args.force_all:
        items_to_rewrite = all_metrics(data)
        print(f"\n  Force-all mode: queuing all {len(items_to_rewrite)} rewritable metrics.")
    else:
        committed = get_committed_data()
        if committed is None:
            print("\n  WARNING: Could not read last git commit. Running in force-all mode.")
            items_to_rewrite = all_metrics(data)
        else:
            items_to_rewrite = find_changed_metrics(data, committed)

    if not items_to_rewrite:
        print("\n  No changes detected vs last git commit. Nothing to rewrite.")
        print("  Use --force-all to rewrite everything regardless.\n")
        sys.exit(0)

    # Print what will be rewritten
    print(f"\n  Metrics queued for rewrite: {len(items_to_rewrite)}\n")
    for item in items_to_rewrite:
        if item["type"] == "metric":
            change = (
                f"{item['old_value']} -> {item['new_value']}"
                if item["old_value"] is not None else item["new_value"]
            )
            print(f"    {item['code']} | {item['section']} | {item['metric']} | {change}")
        else:
            change = (
                f"{item['old_value']} -> {item['new_value']}"
                if item["old_value"] is not None else item["new_value"]
            )
            print(f"    COMMODITY | {item['name']} | {change} {item['unit']}")

    if args.dry_run:
        print("\n  Dry run complete. No API calls made, no files written.\n")
        sys.exit(0)

    # Rewrite stories
    print(f"\n  Calling Claude API ({MODEL})...\n")
    success = 0
    failed = 0

    for item in items_to_rewrite:
        label = (
            f"{item['code']} / {item['metric']}"
            if item["type"] == "metric"
            else f"commodity / {item['name']}"
        )
        try:
            if item["type"] == "metric":
                stories = call_claude_metric(client, item)
                write_metric_story(data, item, stories)
            else:
                stories = call_claude_commodity(client, item)
                write_commodity_story(data, item, stories)

            print(f"    OK  {label}")
            success += 1

        except json.JSONDecodeError as e:
            print(f"    ERR {label} - JSON parse failed: {e}")
            failed += 1
        except anthropic.APIError as e:
            print(f"    ERR {label} - API error: {e}")
            failed += 1
        except Exception as e:
            print(f"    ERR {label} - unexpected error: {e}")
            failed += 1

    # Write updated data.json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n  Rewrote {success} metric(s). Failed: {failed}.")
    print(f"  data.json updated.")
    print(f"\n  Run python3 build.py to assemble and publish.\n")


if __name__ == "__main__":
    main()
