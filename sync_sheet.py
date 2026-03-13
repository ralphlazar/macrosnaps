#!/usr/bin/env python3
"""
sync_sheet.py - MacroSnaps Macro-stats sheet sync
Reads 12 country tabs from the Macro-stats Google Sheet.
Writes 2026F card values and annual historical arrays into data.json.

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

SHEET_ID = "1f9Hwisg00iYk9WNoEqlkBztQlOm3Cl-WcfXQBYHqbLo"
DATA_FILE = "data.json"
TODAY = date.today().isoformat()

COUNTRIES = [
    "USA", "CAN", "GBR", "DEU", "FRA", "ITA",
    "JPN", "CHN", "IND", "BRA", "RUS", "ZAF",
]

# Sheet row name to data.json display key
METRIC_MAP = {
    "GDP_Growth":      "GDP Growth",
    "Inflation":       "Inflation (CPI)",
    "Unemployment":    "Unemployment",
    "Budget_Deficit":  "Budget Deficit",
    "Current_Account": "Current Account",
    "Policy_Rate":     "Policy Rate",
}

# These three get _frozen_historical written (annual bar charts in tooltips)
WRITE_HISTORICAL = {"GDP Growth", "Budget Deficit", "Current Account"}

# ── fetch and parse ───────────────────────────────────────────────────────────

def fetch_tab(sheet_id, tab_name):
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={tab_name}"
    )
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ERROR fetching tab {tab_name}: {e}")
        return None


def parse_tab(csv_text):
    """
    Parse a country tab CSV.
    Returns (years_list, metrics_dict) where metrics_dict is:
        { "GDP_Growth": { "2000": 2.9, "2001": 0.2, ..., "2026F": 2.2 }, ... }

    The gviz CSV export does not include the "2026F" header label even though
    the data exists in the next column. We detect it dynamically by checking
    whether the column immediately after the last labelled year has data.
    Trailing empty padding columns are ignored.
    """
    reader = csv.reader(io.StringIO(csv_text))
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return None, None

    header = rows[0]

    # Collect only non-empty year columns from the header
    year_indices = []
    years = []
    for i, cell in enumerate(header[1:], start=1):
        if cell.strip():
            year_indices.append(i)
            years.append(cell.strip())

    # Check if the column immediately after the last labelled year has data
    # in any metric row - this is the 2026F forecast column
    if years:
        next_idx = year_indices[-1] + 1
        has_forecast = any(
            len(row) > next_idx and
            row[next_idx].strip() not in ("", "n/a", "N/A", "-")
            for row in rows[1:]
        )
        if has_forecast:
            try:
                forecast_label = f"{int(years[-1]) + 1}F"
            except ValueError:
                forecast_label = "2026F"
            year_indices.append(next_idx)
            years.append(forecast_label)

    metrics = {}
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        metric_name = row[0].strip()
        values = {}
        for idx, year in zip(year_indices, years):
            raw = row[idx].strip() if idx < len(row) else ""
            if raw in ("", "n/a", "N/A", "-"):
                values[year] = None
            else:
                try:
                    values[year] = float(raw)
                except ValueError:
                    values[year] = None
        metrics[metric_name] = values

    return years, metrics

# ── formatting ────────────────────────────────────────────────────────────────

def fmt_num(val):
    """Format a number to up to 2 decimal places, stripping trailing zeros."""
    s = f"{val:.2f}".rstrip("0").rstrip(".")
    return s


def fmt_card_value(display_key, val):
    """Format a float as the card display string matching existing data.json conventions."""
    if val is None:
        return None
    if display_key == "GDP Growth":
        sign = "+" if val >= 0 else ""
        return f"{sign}{fmt_num(val)}%"
    elif display_key in ("Budget Deficit", "Current Account"):
        sign = "+" if val > 0 else ""
        return f"{sign}{fmt_num(val)}% GDP"
    else:
        # Inflation (CPI), Unemployment, Policy Rate
        return f"{fmt_num(val)}%"

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    apply_mode = "--apply" in sys.argv
    print(f"\nSync mode: {'APPLY' if apply_mode else 'PREVIEW'}\n")

    with open(DATA_FILE) as f:
        data = json.load(f)

    changes = []  # list of (code, field_label, old_value, new_value)

    for code in COUNTRIES:
        print(f"Fetching {code}...")
        csv_text = fetch_tab(SHEET_ID, code)
        if csv_text is None:
            print(f"  Skipping {code} (fetch failed)\n")
            continue

        years, sheet_metrics = parse_tab(csv_text)
        if sheet_metrics is None:
            print(f"  Skipping {code} (parse failed)\n")
            continue

        if code not in data["countries"]:
            print(f"  Skipping {code} (not found in data.json)\n")
            continue

        country = data["countries"][code]

        for sheet_key, display_key in METRIC_MAP.items():
            if sheet_key not in sheet_metrics:
                print(f"  WARNING: {sheet_key} not found in {code} tab")
                continue

            metric_data = sheet_metrics[sheet_key]

            # ── 1. card value (2026F) ─────────────────────────────────────
            val_2026 = metric_data.get("2026F")
            formatted = fmt_card_value(display_key, val_2026)

            macro_block = country.get("metrics", {}).get("macro", {})
            if display_key in macro_block:
                old_val = macro_block[display_key].get("value")
                if old_val != formatted:
                    changes.append((
                        code,
                        f"card value: {display_key}",
                        old_val,
                        formatted,
                    ))
                    if apply_mode:
                        macro_block[display_key]["value"] = formatted
                        macro_block[display_key]["last_updated"] = TODAY

            # ── 2. _frozen_historical (annual chart metrics only) ─────────
            if display_key in WRITE_HISTORICAL:
                v_array = [metric_data.get(year) for year in years]

                fh = country.get("_frozen_historical", {})
                old_v = fh.get(display_key, {}).get("v", [])

                if old_v != v_array:
                    changes.append((
                        code,
                        f"historical: {display_key}",
                        f"{len(old_v)} points",
                        f"{len(v_array)} points (2000-2026F)",
                    ))
                    if apply_mode:
                        if display_key not in fh:
                            fh[display_key] = {"type": "bar", "annual": True}
                        fh[display_key]["v"] = v_array
                        country["_frozen_historical"] = fh

    # ── summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    if not changes:
        print("No changes detected.")
    else:
        print(f"{len(changes)} change(s) detected:\n")
        for code, field, old, new in changes:
            print(f"  {code}  |  {field}")
            print(f"    {old}  ->  {new}")

    if apply_mode and changes:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\ndata.json updated ({TODAY}). Run build.py to rebuild the site.")
    elif not apply_mode and changes:
        print("\nRun with --apply to write these changes.")

    print()


if __name__ == "__main__":
    main()
