#!/usr/bin/env python3
"""
audit_ritual.py
MacroSnaps daily health report.
Run after build.py --apply as the final step of the daily ritual.

Usage:
    python3 audit_ritual.py              # reads data.json in current directory
    python3 audit_ritual.py --json       # also writes logs/audit_YYYY-MM-DD.json
"""

import json
import os
import sys
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_PATH = "data.json"
LOGS_DIR  = "logs"

COUNTRIES = ["USA", "CAN", "GBR", "DEU", "FRA", "ITA", "JPN", "CHN", "IND", "BRA", "RUS", "ZAF"]
TIERS     = ["beginner", "moderate", "expert"]

MACRO_METRICS  = ["GDP Growth", "Inflation (CPI)", "Unemployment", "Budget Deficit", "Current Account", "Policy Rate"]
MARKET_METRICS = ["Stock Market YTD", "10Y Bond Yield", "Yield Curve"]

# Permanent blank market metrics per country (known gaps -- not flagged)
KNOWN_BLANK_MARKET = {
    "CHN": {"10Y Bond Yield", "Yield Curve"},
    "IND": {"10Y Bond Yield", "Yield Curve"},
    "BRA": {"10Y Bond Yield", "Yield Curve"},
    "RUS": {"10Y Bond Yield", "Yield Curve"},
}

# Permanent blank _frozen_historical entries per country (known gaps -- not flagged)
KNOWN_BLANK_HISTORICAL = {
    "CHN": {"Policy Rate", "Unemployment", "10Y Bond Yield", "Yield Curve"},
    "IND": {"Unemployment", "10Y Bond Yield", "Yield Curve"},
    "BRA": {"Unemployment", "10Y Bond Yield", "Yield Curve"},
    "RUS": {"Unemployment", "10Y Bond Yield", "Yield Curve"},
    "ZAF": {"Unemployment"},
}

COMMODITIES = ["WTI Crude", "Brent Crude", "Natural Gas", "Gold", "Silver", "Copper", "Wheat", "Corn", "Soybeans"]
STALE_MONTHS = 3

def _months_since_jan_2000():
    today = date.today()
    return (today.year - 2000) * 12 + today.month

EXPECTED_SPARK_PTS = _months_since_jan_2000()

GLOBAL_STORY_LABELS = ["Today's Story", "Biggest Movers", "The Connection"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RED   = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def ok(msg):    print(f"  {GREEN}✓{RESET}  {msg}")
def fail(msg):  print(f"  {RED}✗{RESET}  {msg}"); return 1
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}"); return 1

def section(title):
    print(f"\n{BOLD}{title}{RESET}")
    print("  " + "-" * 54)

def is_blank(val):
    if val is None:
        return True
    s = str(val).strip()
    return s == "" or s.upper() == "FAILED" or s.upper() == "NULL" or s == "N/A"

def parse_spark_date(label):
    """Parse a monthly label like '2026-03' into a date (last day of month)."""
    try:
        d = datetime.strptime(label, "%Y-%m")
        # advance to first of next month then back one day
        if d.month == 12:
            return date(d.year + 1, 1, 1) - timedelta(days=1)
        return date(d.year, d.month + 1, 1) - timedelta(days=1)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_build_date(data, issues):
    section("1. Build date")
    today = date.today().strftime("%Y-%m-%d")
    generated = data.get("_meta", {}).get("generated", "")
    if not generated:
        issues += fail("_meta.generated is missing")
    elif not generated.startswith(today):
        issues += fail(f"_meta.generated is {generated!r}, expected today ({today})")
    else:
        ok(f"_meta.generated = {generated}")
    return issues

def check_market_values(data, issues):
    section("2. Market values")
    clean = True
    for code in COUNTRIES:
        country = data["countries"].get(code, {})
        market  = country.get("metrics", {}).get("market", {})
        known_blanks = KNOWN_BLANK_MARKET.get(code, set())

        # FX label varies per country -- find it
        fx_label = next((k for k in market if k.startswith("FX") or "/" in k), None)
        check_labels = MARKET_METRICS + ([fx_label] if fx_label else [])

        for label in check_labels:
            if label in known_blanks:
                continue
            val = market.get(label, {})
            if isinstance(val, dict):
                val = val.get("value")
            if is_blank(val):
                issues += fail(f"{code}  {label}  = {val!r}")
                clean = False

    if clean:
        ok("All market values populated")
    return issues

def check_spark_arrays(data, issues):
    section("3. Spark arrays (_frozen_historical)")
    today = date.today()
    stale_cutoff = date(today.year, today.month, 1) - timedelta(days=STALE_MONTHS * 28)
    clean = True

    for code in COUNTRIES:
        country = data["countries"].get(code, {})
        fh = country.get("_frozen_historical", {})
        known_blanks = KNOWN_BLANK_HISTORICAL.get(code, set())

        for label, entry in fh.items():
            if label in known_blanks:
                continue
            v = entry.get("v", [])
            if not v:
                issues += fail(f"{code}  {label}  spark empty")
                clean = False
                continue
            # find last non-null value
            non_null = [x for x in v if x is not None]
            if not non_null:
                issues += fail(f"{code}  {label}  spark all-null")
                clean = False
                continue

    if clean:
        ok("All spark arrays non-empty")
    return issues

def check_commodities(data, issues):
    section("4. Commodities")
    items = {item["name"]: item for item in data.get("commodities", {}).get("items", [])}
    clean = True

    for name in COMMODITIES:
        item = items.get(name)
        if not item:
            issues += fail(f"{name}  missing entirely")
            clean = False
            continue
        if is_blank(item.get("price")):
            issues += fail(f"{name}  price blank")
            clean = False
        if is_blank(item.get("change")):
            issues += fail(f"{name}  change blank")
            clean = False
        spark = item.get("spark", [])
        if len(spark) < EXPECTED_SPARK_PTS - 3:   # allow up to 3 months of lag
            issues += warn(f"{name}  spark has {len(spark)} pts (expected ~{EXPECTED_SPARK_PTS})")
            clean = False

    if clean:
        ok(f"All 9 commodities have price, change, and ~{EXPECTED_SPARK_PTS}-pt spark")
    return issues

def check_story_completeness(data, issues):
    section("5. Story completeness (all tiers present)")
    clean = True

    for code in COUNTRIES:
        country = data["countries"].get(code, {})
        stories = country.get("stories", {})

        for tier in TIERS:
            text = stories.get(tier, "")
            if is_blank(text):
                issues += fail(f"{code}  story [{tier}] missing")
                clean = False

    if clean:
        ok("All 12 countries have stories at all 3 tiers")
    return issues

def check_story_freshness(data, issues):
    section("6. Story freshness (market metrics updated today)")
    today_str = date.today().strftime("%Y-%m-%d")
    stale = []
    # Use Stock Market YTD as the daily-updated proxy; fall back to any market metric
    PROXY_METRIC = "Stock Market YTD"

    for code in COUNTRIES:
        country = data["countries"].get(code, {})
        market = country.get("metrics", {}).get("market", {})
        proxy = market.get(PROXY_METRIC, {})
        lu = proxy.get("last_updated", "") if isinstance(proxy, dict) else ""
        if not lu:
            # fall back to first available market metric with a last_updated
            for v in market.values():
                if isinstance(v, dict) and v.get("last_updated"):
                    lu = v["last_updated"]
                    break
        if not lu:
            stale.append((code, "no last_updated found on any market metric"))
        elif not lu.startswith(today_str):
            stale.append((code, lu))

    if not stale:
        ok("All 12 countries have market data updated today")
    else:
        for code, val in stale:
            issues += fail(f"{code}  last market update = {val!r} (expected {today_str})")
    return issues

def check_story_mismatches(data, issues):
    section("7. Story mismatches (value_at_generation vs current value)")
    clean = True

    for code in COUNTRIES:
        country = data["countries"].get(code, {})
        macro = country.get("metrics", {}).get("macro", {})

        for metric_name, metric in macro.items():
            if not isinstance(metric, dict):
                continue
            vag = metric.get("value_at_generation")
            val = metric.get("value")
            if vag is not None and vag != val:
                issues += fail(f"{code}  {metric_name}  story written for {vag!r}, current value is {val!r}")
                clean = False

    if clean:
        ok("No story mismatches detected")
    return issues

def check_global_stories(data, issues):
    section("8. Global stories (3 cards x 3 tiers)")
    global_stories = data.get("globalStories", {})
    clean = True

    if not global_stories:
        issues += fail("globalStories missing from data.json")
        return issues

    for tier in TIERS:
        cards = global_stories.get(tier, [])
        if len(cards) < 3:
            issues += fail(f"globalStories[{tier}] has {len(cards)} card(s) (expected 3)")
            clean = False
            continue
        for card in cards[:3]:
            label = card.get("label", "unlabelled")
            body = card.get("body", "")
            if is_blank(body):
                issues += fail(f"Global story [{tier}] [{label}] body missing")
                clean = False

    if clean:
        ok("All 3 global story cards present at all 3 tiers")
    return issues

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MacroSnaps daily ritual audit")
    parser.add_argument("--json", action="store_true", help="Also write machine-readable JSON log")
    parser.add_argument("--data", default=DATA_PATH, help=f"Path to data.json (default: {DATA_PATH})")
    args = parser.parse_args()

    today_str = date.today().strftime("%Y-%m-%d")

    print(f"\n{BOLD}============================================================")
    print(f"  MacroSnaps - Daily Audit")
    print(f"  {today_str}")
    print(f"============================================================{RESET}")

    # Load data.json
    data_path = args.data
    if not os.path.exists(data_path):
        print(f"\n{RED}ERROR: {data_path} not found. Run from the macrosnaps project directory.{RESET}\n")
        sys.exit(1)

    with open(data_path, "r") as f:
        data = json.load(f)

    issues = 0
    issues = check_build_date(data, issues)
    issues = check_market_values(data, issues)
    issues = check_spark_arrays(data, issues)
    issues = check_commodities(data, issues)
    issues = check_story_completeness(data, issues)
    issues = check_story_freshness(data, issues)
    issues = check_story_mismatches(data, issues)
    issues = check_global_stories(data, issues)

    # Summary
    print(f"\n{BOLD}============================================================{RESET}")
    if issues == 0:
        print(f"  {GREEN}{BOLD}All checks passed.{RESET}")
    else:
        print(f"  {RED}{BOLD}{issues} issue(s) found.{RESET} Review the flags above.")
    print(f"{BOLD}============================================================{RESET}\n")

    # Write plain-text log (ANSI codes stripped)
    Path(LOGS_DIR).mkdir(exist_ok=True)
    log_path = os.path.join(LOGS_DIR, f"audit_{today_str}.txt")

    import re
    ansi_escape = re.compile(r'\033\[[0-9;]*m')

    # Collect issues into plain text by re-running checks with a collector
    issue_lines = []

    def collect(msg, prefix):
        issue_lines.append(f"{prefix} {msg}")
        return 1

    # Lightweight re-collect pass (no terminal output)
    _issues = 0
    _today = date.today().strftime("%Y-%m-%d")
    generated = data.get("_meta", {}).get("generated", "")
    if not generated.startswith(_today):
        _issues += collect(f"Build date mismatch: {generated!r}", "✗")

    for code in COUNTRIES:
        country = data["countries"].get(code, {})
        market  = country.get("metrics", {}).get("market", {})
        known_blanks = KNOWN_BLANK_MARKET.get(code, set())
        for label in MARKET_METRICS:
            if label in known_blanks:
                continue
            val = market.get(label, {})
            if isinstance(val, dict):
                val = val.get("value")
            if is_blank(val):
                _issues += collect(f"{code}  {label}  = {val!r}", "✗")

        proxy = market.get("Stock Market YTD", {})
        lu = proxy.get("last_updated", "") if isinstance(proxy, dict) else ""
        if not lu:
            for v in market.values():
                if isinstance(v, dict) and v.get("last_updated"):
                    lu = v["last_updated"]
                    break
        if not lu or not lu.startswith(_today):
            _issues += collect(f"{code}  last market update = {lu!r}", "⚠")

        macro = country.get("metrics", {}).get("macro", {})
        for metric_name, metric in macro.items():
            if not isinstance(metric, dict):
                continue
            vag = metric.get("value_at_generation")
            val = metric.get("value")
            if vag is not None and vag != val:
                _issues += collect(f"{code}  {metric_name}  story written for {vag!r}, current {val!r}", "✗")

    for name in COMMODITIES:
        items = {item["name"]: item for item in data.get("commodities", {}).get("items", [])}
        item = items.get(name)
        if not item or is_blank(item.get("price")):
            _issues += collect(f"Commodity {name} price blank", "✗")

    with open(log_path, "w") as f:
        f.write(f"MacroSnaps Daily Audit - {today_str}\n")
        f.write("=" * 60 + "\n")
        f.write(f"data.json generated : {data.get('_meta', {}).get('generated', 'unknown')}\n")
        f.write(f"Issues found        : {issues}\n")
        f.write("=" * 60 + "\n\n")
        if issue_lines:
            for line in issue_lines:
                f.write(line + "\n")
        else:
            f.write("All checks passed.\n")

    print(f"  Log written: {log_path}\n")

    if issues > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
