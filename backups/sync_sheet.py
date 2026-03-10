#!/usr/bin/env python3
"""
sync_sheet.py - MacroSnaps Google Sheet sync
Fetches your published CSV, maps values to data.json, writes in place.

Usage:
    python3 sync_sheet.py              # preview changes only
    python3 sync_sheet.py --apply      # write to data.json

Run from ~/Downloads/macrosnaps/
"""

import csv
import json
import sys
import io
import urllib.request
from datetime import date

# ── config ────────────────────────────────────────────────────────────────────

SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQgdfggKVeP6013PCtc3_L_hJGLE--b9jiGaU-yMHwKK_iO5o4lPg4dxHvq1hlO3uTb-q_KuiBB8Swj"
    "/pub?output=csv"
)

DATA_FILE = "data.json"

TODAY = date.today().isoformat()

# Maps sheet column name -> (data.json section, metric name, value formatter)
# formatter: a function that takes the raw string and returns the display string
COLUMN_MAP = {
    "GDP_Growth_2026":     ("macro", "GDP Growth",       lambda v: f"+{v}%" if not v.startswith("-") else f"{v}%"),
    "Inflation_2026":      ("macro", "Inflation (CPI)",  lambda v: f"{v}%"),
    "Budget_Deficit_2026": ("macro", "Budget Deficit",   lambda v: f"{v}% GDP"),
    "Current_Account_2026":("macro", "Current Account",  lambda v: f"+{v}% GDP" if not v.startswith("-") else f"{v}% GDP"),
    "Unemployment_2026":   ("macro", "Unemployment",     lambda v: f"{v}%"),
    "Policy_Rate_2026":    ("macro", "Policy Rate",      lambda v: f"{v}%"),
}

# ── helpers ───────────────────────────────────────────────────────────────────

def fetch_csv():
    req = urllib.request.Request(SHEET_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")

def parse_csv(raw):
    reader = csv.DictReader(io.StringIO(raw))
    rows = {}
    for row in reader:
        country = row.get("Country", "").strip().upper()
        if country:
            rows[country] = {k.strip(): v.strip() for k, v in row.items()}
    return rows

def clean_value(v):
    """Strip % signs, spaces, commas so we can compare numerically."""
    return v.replace("%", "").replace(",", "").strip()

def values_differ(old, new):
    """True if the values are meaningfully different (ignore trailing zeros etc.)."""
    try:
        return abs(float(clean_value(old)) - float(clean_value(new))) > 0.001
    except ValueError:
        return old.strip() != new.strip()

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    apply = "--apply" in sys.argv

    print("MacroSnaps sheet sync")
    print(f"Mode: {'APPLY - will write data.json' if apply else 'PREVIEW - no files written'}")
    print(f"Date: {TODAY}")
    print()

    # Fetch sheet
    print("Fetching sheet...", end=" ", flush=True)
    try:
        raw = fetch_csv()
        print("OK")
    except Exception as e:
        print(f"FAILED\nError: {e}")
        sys.exit(1)

    sheet_rows = parse_csv(raw)
    if not sheet_rows:
        print("ERROR: No rows parsed from sheet. Check the URL is published as CSV.")
        sys.exit(1)

    print(f"Sheet rows found: {list(sheet_rows.keys())}")
    print()

    # Load data.json
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    changes = []
    skipped = []
    missing_countries = []
    missing_columns = []

    for country_code, row in sheet_rows.items():
        if country_code not in data["countries"]:
            missing_countries.append(country_code)
            continue

        for col, (section, metric_name, fmt) in COLUMN_MAP.items():
            if col not in row:
                if col not in missing_columns:
                    missing_columns.append(col)
                continue

            raw_val = row[col].strip()
            if not raw_val:
                skipped.append(f"{country_code} / {metric_name}: blank in sheet, skipping")
                continue

            try:
                new_display = fmt(raw_val)
            except Exception as e:
                skipped.append(f"{country_code} / {metric_name}: format error ({e}), skipping")
                continue

            metric = data["countries"][country_code]["metrics"][section].get(metric_name)
            if metric is None:
                skipped.append(f"{country_code} / {metric_name}: not found in data.json, skipping")
                continue

            old_display = metric["value"]

            if values_differ(old_display, new_display):
                changes.append({
                    "country": country_code,
                    "metric": metric_name,
                    "old": old_display,
                    "new": new_display,
                    "metric_ref": metric,
                })
            # else: no change, silently skip

    # Print report
    if missing_countries:
        print(f"WARNING: Sheet has countries not in data.json: {missing_countries}")

    if missing_columns:
        print(f"NOTE: Columns not found in sheet (will be skipped): {missing_columns}")
        print()

    if skipped:
        print("Skipped (no action needed):")
        for s in skipped:
            print(f"  - {s}")
        print()

    if not changes:
        print("No changes detected. data.json is already up to date with the sheet.")
        return

    print(f"{'Changes to apply' if apply else 'Changes detected'} ({len(changes)}):")
    print()
    col_w = max(len(c["country"]) + len(c["metric"]) + 3 for c in changes)
    for c in changes:
        label = f"{c['country']} / {c['metric']}"
        print(f"  {label:<{col_w}}  {c['old']:<14} ->  {c['new']}")

    print()

    if not apply:
        print("Run with --apply to write these changes to data.json.")
        print("Then run: python3 build.py && git add -A && git commit -m \"Sheet sync $(date +%Y-%m-%d)\"")
        return

    # Apply changes
    for c in changes:
        c["metric_ref"]["value"] = c["new"]
        c["metric_ref"]["last_updated"] = TODAY

    # Update _meta
    data["_meta"]["generated"] = TODAY
    data["_meta"]["built_at"] = f"{TODAY} (sheet sync)"

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"data.json updated with {len(changes)} change(s).")
    print()
    print("Next steps:")
    print(f'  python3 build.py && git add -A && git commit -m "Sheet sync {TODAY}"')
    print(f'  git push origin master')


if __name__ == "__main__":
    main()
