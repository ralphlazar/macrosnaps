#!/usr/bin/env python3
"""
patch_data_json_startdates.py
==============================
Adds 'startDate' to every monthly _frozen_historical series in data.json.

startDate pins the data anchor explicitly so the JS can left-align from
the correct historical month, independent of array length or build date.

Two reference counts are used:
  - Inflation (CPI): frozen April 2025 (label count = 304)
  - All other series: live, ending April 2026 (label count = 316)

Annual (bar-type) series use a separate label array and are not touched.

Run from the macrosnaps repo directory:
    python3 ~/Downloads/patch_data_json_startdates.py
"""

import json, sys, os

DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    print(f"FATAL: {DATA_FILE} not found. Run from the macrosnaps repo directory.")
    sys.exit(1)

# Label array anchor: Jan 2000 = index 0
LABEL_ORIGIN_YEAR  = 2000
LABEL_ORIGIN_MONTH = 1  # January

# Reference label counts
LIVE_COUNT     = 316  # Jan 2000 → Apr 2026 (current build)
FREEZE_CPI_COUNT = 304  # Jan 2000 → Apr 2025 (CPI series frozen then)

def label_index_to_ym(idx):
    """Convert a 0-based label index (Jan 2000 = 0) to 'YYYY-MM' string."""
    total_months = LABEL_ORIGIN_YEAR * 12 + (LABEL_ORIGIN_MONTH - 1) + idx
    y = total_months // 12
    m = total_months % 12 + 1
    return f"{y}-{m:02d}"

def compute_start_date(metric_name, n_pts):
    """Return the correct 'YYYY-MM' startDate for a series."""
    if metric_name == "Inflation (CPI)":
        ref = FREEZE_CPI_COUNT
    else:
        ref = LIVE_COUNT
    start_idx = ref - n_pts
    if start_idx < 0:
        # More data points than labels — clamp to index 0
        start_idx = 0
    return label_index_to_ym(start_idx)

# ── Load ────────────────────────────────────────────────────────────────────
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

countries = data.get("countries", {})

added   = 0
skipped = 0

print(f"\nPatching {DATA_FILE} — adding startDate to _frozen_historical series...\n")

for code, country in sorted(countries.items()):
    fh = country.get("_frozen_historical")
    if not fh:
        continue
    for metric, cfg in fh.items():
        if not isinstance(cfg, dict):
            continue
        v = cfg.get("v", [])
        if not v:
            continue

        # Skip annual (bar) series — they use a different label array
        if cfg.get("type") == "bar" or cfg.get("annual"):
            skipped += 1
            continue

        n = len(v)
        start_date = compute_start_date(metric, n)
        cfg["startDate"] = start_date
        added += 1
        print(f"  [{code}] {metric:<25} {n:>4} pts  startDate={start_date}")

print(f"\n  Added startDate to {added} series, skipped {skipped} annual series.")

# ── Write ────────────────────────────────────────────────────────────────────
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"  Written: {DATA_FILE}\n")
print("  Done. Run patch_shell_alignment.py next.\n")
