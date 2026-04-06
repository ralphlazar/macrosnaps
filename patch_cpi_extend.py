#!/usr/bin/env python3
"""
patch_cpi_extend.py
====================
Extends each country's _frozen_historical['Inflation (CPI)'].v with the
newer monthly_actuals.inflation values, eliminating the gap at the end of
the chart.

Strategy: find the first (newest) monthly_actuals entry whose value is
within 0.10% of the frozen historical tail value — this marks the
overlap point. All entries before that index are newer; append them
oldest-first to the frozen array.

Countries where no reliable splice point is found (IND, JPN, RUS) are
skipped and flagged for manual review.

Run from the macrosnaps repo directory:
    python3 ~/Downloads/patch_cpi_extend.py
"""

import json, sys, os

DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    print(f"FATAL: {DATA_FILE} not found. Run from the macrosnaps repo directory.")
    sys.exit(1)

TOLERANCE = 0.05  # % — acceptable difference for value-match splice

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

countries = data.get("countries", {})

print(f"\nExtending _frozen_historical Inflation (CPI) arrays with monthly_actuals...\n")
print(f"  {'Code':<5} {'Before':>7} {'Appended':>9} {'After':>7}  Notes")
print(f"  {'-'*55}")

skipped = []

for code in sorted(countries.keys()):
    c = countries[code]
    ma = c.get("monthly_actuals", {}).get("inflation", [])
    fh = c.get("_frozen_historical", {}).get("Inflation (CPI)")

    if not fh or not fh.get("v"):
        print(f"  {code:<5}  no frozen historical — skipped")
        continue
    if not ma:
        print(f"  {code:<5}  no monthly_actuals.inflation — skipped")
        continue

    fh_v = fh["v"]
    tail_val = fh_v[-1]
    n_before = len(fh_v)

    # Find FIRST (newest) entry in monthly_actuals within tolerance of tail_val
    match_idx = None
    for i, entry in enumerate(ma):
        val = entry["value"] if isinstance(entry, dict) else entry
        if abs(val - tail_val) <= TOLERANCE:
            match_idx = i
            break

    if match_idx is None:
        note = f"no splice match for tail={tail_val:.2f} — manual review needed"
        print(f"  {code:<5} {n_before:>7} {'':>9} {'':>7}  *** {note}")
        skipped.append((code, note))
        continue

    # Entries [0 .. match_idx-1] are newer than the frozen tail
    newer_entries = ma[:match_idx]
    if not newer_entries:
        print(f"  {code:<5} {n_before:>7} {'0':>9} {n_before:>7}  already current")
        continue

    # Reverse to oldest-first, extract values
    newer_vals = [
        round(e["value"] if isinstance(e, dict) else e, 4)
        for e in reversed(newer_entries)
    ]

    fh["v"] = fh_v + newer_vals
    n_after = len(fh["v"])

    print(f"  {code:<5} {n_before:>7} {len(newer_vals):>9} {n_after:>7}")

print()

if skipped:
    print("  Countries requiring manual CPI data review:")
    for code, note in skipped:
        print(f"    {code}: {note}")
    print()

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"  Written: {DATA_FILE}")
print(f"\n  Done. Run build.py to rebuild.\n")
