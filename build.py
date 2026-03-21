#!/usr/bin/env python3
"""
MacroSnaps build.py
===================
Validates data.json, detects changes vs yesterday's backup,
merges shell + data → final macrosnaps-globe.html, and
stamps today's date automatically.

Usage:
    python3 build.py

Requires: data.json and macrosnaps-shell.html in the same folder.
Output:   macrosnaps-globe.html (ready to publish)
"""

import json
import sys
import os
import re
import shutil
from datetime import date, datetime
from copy import deepcopy

# ── Config ──────────────────────────────────────────────────────────────────
SHELL_FILE   = "macrosnaps-shell.html"
DATA_FILE    = "data.json"
OUTPUT_FILE  = "index.html"
BACKUP_DIR   = "backups"
TODAY        = date.today().isoformat()          # e.g. "2026-03-08"
NOW          = datetime.now().strftime("%Y-%m-%d %H:%M")

# All 12 country codes expected
EXPECTED_COUNTRIES = {"USA","CAN","GBR","JPN","DEU","FRA","ITA","CHN","IND","ZAF","BRA","RUS"}

# The 6 macro metrics every country must have
MACRO_METRICS = [
    "GDP Growth","Inflation (CPI)","Unemployment",
    "Budget Deficit","Current Account","Policy Rate"
]

# The 4 market metrics every country must have (FX key varies by country)
MARKET_METRICS_BASE = [
    "Stock Market YTD","10Y Bond Yield","Yield Curve"
]

# FX key per country
FX_KEYS = {
    "USA":"USD/DXY","CAN":"CAD/USD","GBR":"GBP/USD","JPN":"USD/JPY",
    "DEU":"EUR/USD","FRA":"EUR/USD","ITA":"EUR/USD","CHN":"USD/CNY",
    "IND":"USD/INR","ZAF":"USD/ZAR","BRA":"USD/BRL","RUS":"USD/RUB"
}

# Valid tiers
VALID_TIERS = {"daily","weekly","structural"}

# Commodity names expected
EXPECTED_COMMODITIES = {
    "WTI Crude","Brent Crude","Natural Gas",
    "Gold","Silver","Copper",
    "Wheat","Corn","Soybeans"
}

STORY_LEVELS = ["beginner","moderate","expert"]

# ── Helpers ─────────────────────────────────────────────────────────────────
errors   = []
warnings = []

def err(msg):  errors.append(f"  ✗ {msg}")
def warn(msg): warnings.append(f"  ⚠  {msg}")
def ok(msg):   print(f"  ✓ {msg}")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Load & parse
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "═"*60)
print("  MacroSnaps Build Script")
print(f"  {NOW}")
print("═"*60)

# Check files exist
for fname in [SHELL_FILE, DATA_FILE]:
    if not os.path.exists(fname):
        print(f"\n  FATAL: '{fname}' not found in current directory.\n")
        sys.exit(1)

# Load data.json
with open(DATA_FILE, "r", encoding="utf-8") as f:
    raw = f.read()

try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"\n  FATAL: data.json is not valid JSON.\n  Error: {e}\n")
    sys.exit(1)

ok("data.json parsed as valid JSON")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Schema validation
# ════════════════════════════════════════════════════════════════════════════
print("\n── Validating schema ──────────────────────────────────────")

# Top-level keys
required_top = {"_meta","countries","commodities","globalStories"}
missing_top = required_top - set(data.keys())
if missing_top:
    for k in missing_top: err(f"Top-level key missing: '{k}'")
else:
    ok("Top-level keys present")

# _meta
meta = data.get("_meta", {})
if "generated" not in meta:
    err("_meta.generated is missing")
else:
    ok(f"_meta.generated = {meta['generated']}")

# ── Countries ────────────────────────────────────────────────────────────
countries = data.get("countries", {})
found_codes = set(countries.keys())
missing_countries = EXPECTED_COUNTRIES - found_codes
extra_countries   = found_codes - EXPECTED_COUNTRIES

if missing_countries:
    err(f"Missing countries: {sorted(missing_countries)}")
else:
    ok(f"All 12 countries present")

if extra_countries:
    warn(f"Unexpected country codes: {sorted(extra_countries)}")

# Validate each country
for code in EXPECTED_COUNTRIES:
    c = countries.get(code)
    if not c:
        continue  # already flagged above

    prefix = f"[{code}]"

    # Required fields
    for field in ["code","name","flag","lat","lon","weather","metrics","stories"]:
        if field not in c:
            err(f"{prefix} missing field '{field}'")

    # Metrics structure
    metrics = c.get("metrics", {})
    macro   = metrics.get("macro", {})
    market  = metrics.get("market", {})

    # Macro metrics
    for m in MACRO_METRICS:
        if m not in macro:
            err(f"{prefix} macro metric missing: '{m}'")
        else:
            entry = macro[m]
            if not isinstance(entry, dict):
                err(f"{prefix} macro['{m}'] should be dict with value/tier/last_updated, got {type(entry).__name__}")
            else:
                if "value" not in entry:
                    err(f"{prefix} macro['{m}'].value missing")
                if "tier" not in entry:
                    err(f"{prefix} macro['{m}'].tier missing")
                elif entry["tier"] not in VALID_TIERS:
                    err(f"{prefix} macro['{m}'].tier invalid: '{entry['tier']}' (must be one of {VALID_TIERS})")
                if "last_updated" not in entry:
                    warn(f"{prefix} macro['{m}'].last_updated missing")
                # Story mismatch guard: story must have been written for the current value
                vag = entry.get("value_at_generation")
                if vag is not None and str(vag).strip() != str(entry.get("value","")).strip():
                    err(f"{prefix} macro['{m}'] story mismatch — written for '{vag}', current value is '{entry.get('value')}'. Re-run update_stories.py for this metric.")

    # Market metrics (base set)
    for m in MARKET_METRICS_BASE:
        if m not in market:
            err(f"{prefix} market metric missing: '{m}'")

    # FX key
    expected_fx = FX_KEYS.get(code)
    if expected_fx and expected_fx not in market:
        err(f"{prefix} FX metric missing: '{expected_fx}'")

    # Stories
    stories = c.get("stories", {})
    for lv in STORY_LEVELS:
        s = stories.get(lv, [])
        if not isinstance(s, list):
            err(f"{prefix} stories.{lv} must be a list")
        elif len(s) == 0:
            err(f"{prefix} stories.{lv} is empty — at least 1 story required")
        elif len(s) < 3:
            warn(f"{prefix} stories.{lv} has only {len(s)} story/stories (expected 3)")

    # USA-specific: validate per-metric story fields
    if code == "USA":
        for sec in ["macro", "market"]:
            for mname, mentry in metrics.get(sec, {}).items():
                if not isinstance(mentry, dict): continue
                if "story" not in mentry:
                    err(f"[USA] {sec}['{mname}'].story missing")
                else:
                    for lv in STORY_LEVELS:
                        if lv not in mentry["story"] or not mentry["story"][lv]:
                            err(f"[USA] {sec}['{mname}'].story.{lv} missing or empty")

# ── Commodities ──────────────────────────────────────────────────────────
commodities = data.get("commodities", {})
if "items" not in commodities:
    err("commodities.items missing")
else:
    items = commodities["items"]
    found_comm = {i.get("name") for i in items}
    missing_comm = EXPECTED_COMMODITIES - found_comm
    if missing_comm:
        err(f"Missing commodity items: {sorted(missing_comm)}")
    else:
        ok(f"All 9 commodity items present")

    for item in items:
        name = item.get("name","?")
        for field in ["price","change","spark"]:
            if field not in item:
                err(f"commodity '{name}' missing '{field}'")
        if "price" in item:
            p = item["price"]
            if not isinstance(p, (int, float)):
                err(f"commodity '{name}' price must be a number, got '{p}'")
            elif p <= 0:
                err(f"commodity '{name}' price is <= 0: {p}")
        if "spark" in item:
            spark = item["spark"]
            if not isinstance(spark, list):
                err(f"commodity '{name}' spark must be a list")
            elif len(spark) < 2:
                err(f"commodity '{name}' spark too short (need at least 2 points)")

if "asOf" not in commodities:
    warn("commodities.asOf missing")
if "weather" not in commodities:
    warn("commodities.weather missing")

# Commodity stories
comm_stories = commodities.get("stories", {})
for lv in STORY_LEVELS:
    s = comm_stories.get(lv, [])
    if not s:
        warn(f"commodities.stories.{lv} is empty")

# ── Global stories ────────────────────────────────────────────────────────
global_stories = data.get("globalStories", {})
for lv in STORY_LEVELS:
    s = global_stories.get(lv, [])
    if not isinstance(s, list):
        err(f"globalStories.{lv} must be a list")
    elif len(s) == 0:
        err(f"globalStories.{lv} is empty — 3 stories required")
    elif len(s) < 3:
        warn(f"globalStories.{lv} has only {len(s)} story/stories (3 recommended)")
    else:
        for i, story in enumerate(s):
            if not isinstance(story, dict):
                err(f"globalStories.{lv}[{i}] must be a dict with icon/label/body/source")
            else:
                for field in ["icon","label","body","source"]:
                    if field not in story:
                        err(f"globalStories.{lv}[{i}] missing '{field}'")

if not errors:
    ok("Schema validation passed — all required fields present and valid")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Change detection vs yesterday's backup
# ════════════════════════════════════════════════════════════════════════════
print("\n── Change detection ────────────────────────────────────────")

changed_metrics  = []
changed_stories  = []
changed_comms    = []

# Find most recent backup
yesterday_file = None
if os.path.isdir(BACKUP_DIR):
    backups = sorted([
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith("data_") and f.endswith(".json")
    ], reverse=True)
    if backups:
        yesterday_file = os.path.join(BACKUP_DIR, backups[0])

if yesterday_file and os.path.exists(yesterday_file):
    print(f"  Comparing against backup: {yesterday_file}")
    with open(yesterday_file) as f:
        old = json.load(f)

    # Compare country metrics
    for code in EXPECTED_COUNTRIES:
        c_new = data.get("countries", {}).get(code, {})
        c_old = old.get("countries", {}).get(code, {})
        for group in ["macro","market"]:
            new_group = c_new.get("metrics", {}).get(group, {})
            old_group = c_old.get("metrics", {}).get(group, {})
            for metric_name, new_entry in new_group.items():
                new_val = new_entry.get("value") if isinstance(new_entry, dict) else new_entry
                old_entry = old_group.get(metric_name, {})
                old_val = old_entry.get("value") if isinstance(old_entry, dict) else old_entry
                if str(new_val) != str(old_val):
                    changed_metrics.append(f"{code}.{group}.{metric_name}: {old_val!r} → {new_val!r}")

    # Compare stories
    for code in EXPECTED_COUNTRIES:
        c_new = data.get("countries",{}).get(code,{})
        c_old = old.get("countries",{}).get(code,{})
        for lv in STORY_LEVELS:
            new_s = c_new.get("stories",{}).get(lv,[])
            old_s = c_old.get("stories",{}).get(lv,[])
            if new_s != old_s:
                changed_stories.append(f"{code}.stories.{lv}")

    # Compare commodity prices
    new_items = {i["name"]:i for i in data.get("commodities",{}).get("items",[])}
    old_items = {i["name"]:i for i in old.get("commodities",{}).get("items",[])}
    for name, ni in new_items.items():
        oi = old_items.get(name, {})
        if str(ni.get("price")) != str(oi.get("price")):
            changed_comms.append(f"commodity.{name}: {oi.get('price')} → {ni.get('price')}")

    print(f"  Changed metrics   : {len(changed_metrics)}")
    print(f"  Changed stories   : {len(changed_stories)}")
    print(f"  Changed commodities: {len(changed_comms)}")

    if changed_metrics:
        print("\n  Metric changes:")
        for c in changed_metrics[:20]:
            print(f"    {c}")
        if len(changed_metrics) > 20:
            print(f"    ... and {len(changed_metrics)-20} more")
    if changed_stories:
        print("\n  Story changes:")
        for c in changed_stories:
            print(f"    {c}")
    if changed_comms:
        print("\n  Commodity price changes:")
        for c in changed_comms:
            print(f"    {c}")

    if not changed_metrics and not changed_stories and not changed_comms:
        warn("No changes detected vs yesterday — is data.json up to date?")
else:
    print("  No backup found — skipping change detection.")
    print("  (First run, or backup folder is empty.)")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Abort if validation errors
# ════════════════════════════════════════════════════════════════════════════
if errors:
    print("\n── Validation FAILED ───────────────────────────────────────")
    for e in errors:
        print(e)
    if warnings:
        print("\n  Warnings:")
        for w in warnings: print(w)
    print(f"\n  ✗ BUILD ABORTED — fix the {len(errors)} error(s) above, then re-run.\n")
    sys.exit(1)

if warnings:
    print("\n── Warnings ────────────────────────────────────────────────")
    for w in warnings: print(w)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Merge shell + data → output
# ════════════════════════════════════════════════════════════════════════════
print("\n── Building output ─────────────────────────────────────────")

# Read shell
with open(SHELL_FILE, "r", encoding="utf-8") as f:
    shell = f.read()

# Stamp today's date in the <title> and in a data attribute
# Update <title>
shell = re.sub(
    r'<title>.*?</title>',
    f'<title>MacroSnaps — Global Economic Dashboard — {TODAY}</title>',
    shell
)

# Stamp today's date into data before inlining

# Inline data.json into the HTML so it works as a standalone local file.
# Replace the fetch('data.json') call with a Promise.resolve() over the
# inlined JSON payload — no server required, works via file:// protocol.
data_json_str = json.dumps(data, ensure_ascii=False)

FETCH_OLD = (
    "fetch('data.json')\n"
    "  .then(r => { if(!r.ok) throw new Error('data.json not found: ' + r.status); return r.json(); })\n"
    "  .then(data => {"
)
FETCH_NEW = (
    "// data.json inlined by build.py — standalone file, no server needed\n"
    "Promise.resolve(window.__MACROSNAPS_DATA__)\n"
    "  .then(data => {"
)

if FETCH_OLD not in shell:
    print("  WARNING: Could not find fetch block to replace — output may still require a server.")
else:
    shell = shell.replace(FETCH_OLD, FETCH_NEW)
    ok("Inlined data.json into HTML (standalone mode)")

# Inject the data payload as a <script> block just before </body>
inline_script = (
    f"\n<script>\n"
    f"// Inlined by build.py on {NOW}\n"
    f"window.__MACROSNAPS_DATA__ = {data_json_str};\n"
    f"</script>\n"
)
shell = shell.replace("</head>", inline_script + "</head>", 1)

# Write the output
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(shell)

ok(f"Written: {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE)//1024} KB)")

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
ok(f"Stamped _meta.generated = {TODAY} in data.json")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Backup data.json
# ════════════════════════════════════════════════════════════════════════════
os.makedirs(BACKUP_DIR, exist_ok=True)
backup_path = os.path.join(BACKUP_DIR, f"data_{TODAY}.json")
shutil.copy2(DATA_FILE, backup_path)
ok(f"Backup saved: {backup_path}")

# Prune backups older than 30 days
all_backups = sorted([
    f for f in os.listdir(BACKUP_DIR)
    if f.startswith("data_") and f.endswith(".json")
])
if len(all_backups) > 30:
    for old_b in all_backups[:-30]:
        os.remove(os.path.join(BACKUP_DIR, old_b))
    ok(f"Pruned {len(all_backups)-30} old backup(s), keeping 30 days")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Summary
# ════════════════════════════════════════════════════════════════════════════
print("\n── Summary ─────────────────────────────────────────────────")
print(f"  Date stamped   : {TODAY}")
print(f"  Countries      : {len(countries)}/12")
print(f"  Commodities    : {len(data['commodities'].get('items',[]))}/9")
print(f"  Metric changes : {len(changed_metrics)}")
print(f"  Story changes  : {len(changed_stories)}")
print(f"  Comm changes   : {len(changed_comms)}")
print(f"  Output         : {OUTPUT_FILE}")
print(f"  Backup         : {backup_path}")
print("\n  ✓ BUILD SUCCESSFUL — {OUTPUT_FILE} is ready to publish.\n".format(
    OUTPUT_FILE=OUTPUT_FILE
))

# ════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Auto git commit
# ════════════════════════════════════════════════════════════════════════════
import subprocess
commit_msg = f"Build {TODAY} — auto commit"
result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
if result.returncode != 0:
    print(f"  ⚠  git add failed: {result.stderr.strip()}")
else:
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            print("  git: nothing to commit, working tree clean")
        else:
            print(f"  ⚠  git commit failed: {result.stderr.strip()}")
    else:
        print(f"  ✓ git commit: {commit_msg}")
        result = subprocess.run(["git", "push", "origin", "master"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠  git push failed: {result.stderr.strip()}")
        else:
            print("  ✓ git push: origin master")
